import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from openai import OpenAI
from pypdf import PdfReader
from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import DocumentStatus, KnowledgeChunk, UploadedDocument, User


@dataclass(frozen=True)
class TextChunk:
    content: str
    source_page: int | None = None


class KnowledgeService:
    allowed_suffixes = {".pdf", ".txt", ".md"}
    allowed_content_types = {"application/pdf", "text/plain", "text/markdown", "application/octet-stream"}

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    async def upload(self, db: Session, user: User, organization_id: UUID, file: UploadFile) -> UploadedDocument:
        safe_name = Path(file.filename or "document.txt").name
        self._validate_filename(safe_name)
        self._validate_content_type(file.content_type)
        body = await file.read()
        if len(body) > self.settings.max_upload_bytes:
            raise ValueError(f"Upload exceeds {self.settings.max_upload_bytes} byte limit")
        user_dir = Path(self.settings.upload_dir) / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        storage_path = user_dir / safe_name
        storage_path.write_bytes(body)

        document = UploadedDocument(
            owner_id=user.id,
            organization_id=organization_id,
            filename=safe_name,
            content_type=file.content_type,
            storage_path=str(storage_path),
            status=DocumentStatus.pending,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    def process_document(self, db: Session, document_id: UUID) -> UploadedDocument:
        document = db.get(UploadedDocument, document_id)
        if not document:
            raise RuntimeError("Document not found")

        document.status = DocumentStatus.processing
        document.processing_error = None
        db.commit()

        try:
            db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
            chunks = self.chunk_text(self.extract_text(Path(document.storage_path)))
            for index, chunk in enumerate(chunks):
                embedding = self.embed(chunk.content)
                knowledge_chunk = KnowledgeChunk(
                    document_id=document.id,
                    owner_id=document.owner_id,
                    organization_id=document.organization_id,
                    content=chunk.content,
                    chunk_index=index,
                    source_page=chunk.source_page,
                    token_count=self.estimate_tokens(chunk.content),
                    embedding_model=self.settings.openai_embedding_model,
                    embedding=embedding,
                )
                db.add(knowledge_chunk)
                db.flush()
                self._store_pgvector_embedding(db, knowledge_chunk.id, embedding)
            document.status = DocumentStatus.ready
            document.chunk_count = len(chunks)
            document.processed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(document)
            return document
        except Exception as exc:
            document.status = DocumentStatus.failed
            document.processing_error = str(exc)
            db.commit()
            raise

    def search(self, db: Session, organization_id: UUID, query: str, limit: int = 5) -> list[dict]:
        chunks = db.scalars(
            select(KnowledgeChunk)
            .join(UploadedDocument, UploadedDocument.id == KnowledgeChunk.document_id)
            .where(KnowledgeChunk.organization_id == organization_id, UploadedDocument.status == DocumentStatus.ready)
        ).all()
        query_embedding = self.embed(query)
        ranked = sorted(chunks, key=lambda chunk: self.similarity(query_embedding, chunk.embedding or []), reverse=True)[:limit]
        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": chunk.document.filename if chunk.document else "Unknown source",
                "content": chunk.content,
                "score": round(self.similarity(query_embedding, chunk.embedding or []), 4),
                "source_page": chunk.source_page,
            }
            for chunk in ranked
        ]

    def answer(self, db: Session, organization_id: UUID, question: str, model: str | None = None) -> tuple[str, list[dict]]:
        citations = self.search(db, organization_id, question, limit=4)
        context = "\n\n".join(f"[{index + 1}] {item['content']}" for index, item in enumerate(citations))

        if self.client and context:
            response = self.client.chat.completions.create(
                model=model or self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Answer using only the provided company knowledge. Cite sources inline as [1], [2], etc.",
                    },
                    {"role": "user", "content": f"Question: {question}\n\nKnowledge:\n{context}"},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or "No answer generated.", citations

        if not context:
            return "No relevant knowledge base content was found. Upload product, pricing, or FAQ documents first.", []
        return f"Based on uploaded knowledge: {context[:900]}", citations

    def embed(self, text: str) -> list[float]:
        if self.client:
            response = self.client.embeddings.create(model=self.settings.openai_embedding_model, input=text)
            return response.data[0].embedding
        return self.local_embedding(text)

    def extract_text(self, path: Path) -> list[tuple[str, int | None]]:
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            return [(page.extract_text() or "", index + 1) for index, page in enumerate(reader.pages)]
        return [(path.read_text(encoding="utf-8", errors="ignore"), None)]

    def chunk_text(self, pages: list[tuple[str, int | None]], size: int = 1200, overlap: int = 160) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        for text, page in pages:
            clean = " ".join(text.split())
            if not clean:
                continue
            start = 0
            while start < len(clean):
                chunks.append(TextChunk(content=clean[start : start + size], source_page=page))
                start += size - overlap
        return chunks or [TextChunk(content="No extractable text found in this document.")]

    @staticmethod
    def similarity(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def local_embedding(text: str, dimensions: int = 1536) -> list[float]:
        vector = [0.0] * dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def _validate_filename(self, filename: str) -> None:
        if Path(filename).suffix.lower() not in self.allowed_suffixes:
            raise ValueError("Only PDF, text, and markdown uploads are supported")

    def _validate_content_type(self, content_type: str | None) -> None:
        if content_type and content_type not in self.allowed_content_types:
            raise ValueError("Unsupported upload content type")

    @staticmethod
    def _store_pgvector_embedding(db: Session, chunk_id: UUID, embedding: list[float]) -> None:
        if db.bind is None or db.bind.dialect.name != "postgresql":
            return
        vector_literal = "[" + ",".join(str(value) for value in embedding) + "]"
        db.execute(
            text("UPDATE knowledge_chunks SET embedding_vector = CAST(:embedding AS vector) WHERE id = :chunk_id"),
            {"embedding": vector_literal, "chunk_id": chunk_id},
        )
