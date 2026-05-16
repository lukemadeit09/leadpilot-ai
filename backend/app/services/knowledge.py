import math
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from openai import OpenAI
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import KnowledgeChunk, UploadedDocument, User


class KnowledgeService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    async def upload(self, db: Session, user: User, organization_id: UUID, file: UploadFile) -> UploadedDocument:
        user_dir = Path(self.settings.upload_dir) / str(user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename or "document.pdf").name
        storage_path = user_dir / safe_name
        storage_path.write_bytes(await file.read())

        document = UploadedDocument(
            owner_id=user.id,
            organization_id=organization_id,
            filename=safe_name,
            content_type=file.content_type,
            storage_path=str(storage_path),
        )
        db.add(document)
        db.flush()

        text = self._extract_text(storage_path)
        for index, chunk in enumerate(self._chunk_text(text)):
            db.add(
                KnowledgeChunk(
                    document_id=document.id,
                    owner_id=user.id,
                    organization_id=organization_id,
                    content=chunk,
                    chunk_index=index,
                    embedding=self._embed(chunk),
                )
            )
        db.commit()
        db.refresh(document)
        return document

    def answer(self, db: Session, organization_id: UUID, question: str) -> tuple[str, list[str]]:
        chunks = db.scalars(select(KnowledgeChunk).where(KnowledgeChunk.organization_id == organization_id)).all()
        ranked = self._rank(question, chunks)[:4]
        context = "\n\n".join(chunk.content for chunk in ranked)
        sources = [chunk.document.filename for chunk in ranked if chunk.document]

        if self.client and context:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "Answer using only the provided company knowledge. Be concise and practical."},
                    {"role": "user", "content": f"Question: {question}\n\nKnowledge:\n{context}"},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or "No answer generated.", sources

        if not context:
            return "No relevant knowledge base content was found. Upload product, pricing, or FAQ documents first.", []
        return f"Based on uploaded knowledge: {context[:700]}", sources

    def _embed(self, text: str) -> list[float] | None:
        if not self.client:
            return None
        response = self.client.embeddings.create(model=self.settings.openai_embedding_model, input=text)
        return response.data[0].embedding

    def _extract_text(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _chunk_text(text: str, size: int = 1200, overlap: int = 160) -> list[str]:
        clean = " ".join(text.split())
        if not clean:
            return ["No extractable text found in this document."]
        chunks = []
        start = 0
        while start < len(clean):
            chunks.append(clean[start : start + size])
            start += size - overlap
        return chunks

    def _rank(self, question: str, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        query_embedding = self._embed(question)
        if query_embedding and any(chunk.embedding for chunk in chunks):
            return sorted(chunks, key=lambda chunk: self._cosine(query_embedding, chunk.embedding or []), reverse=True)
        terms = {term.lower() for term in question.split() if len(term) > 2}
        return sorted(chunks, key=lambda chunk: sum(term in chunk.content.lower() for term in terms), reverse=True)

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
