from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentStatus, KnowledgeChunk, UploadedDocument
from app.services.knowledge import KnowledgeService
from tests.conftest import auth_headers, register_user


def test_chunking_preserves_page_metadata() -> None:
    service = KnowledgeService()
    chunks = service.chunk_text([("Pricing details " * 120, 3)], size=200, overlap=40)

    assert len(chunks) > 1
    assert all(chunk.source_page == 3 for chunk in chunks)
    assert all(chunk.content for chunk in chunks)


def test_local_embeddings_rank_relevant_chunks() -> None:
    service = KnowledgeService()
    pricing = service.local_embedding("pricing quote contract annual plan")
    query = service.local_embedding("pricing quote")
    support = service.local_embedding("onboarding support implementation")

    assert service.similarity(query, pricing) > service.similarity(query, support)


def test_upload_processes_text_document_and_answers_with_citations(client: TestClient, db_session: Session) -> None:
    token = register_user(client, email="rag@example.com")["access_token"]

    upload = client.post(
        "/knowledge/upload",
        headers=auth_headers(token),
        files={"file": ("pricing.txt", BytesIO(b"Our Pro plan pricing is $50 per month and includes five seats."), "text/plain")},
    )

    assert upload.status_code == 200, upload.text
    document = upload.json()
    assert document["status"] == "ready"
    assert document["chunk_count"] == 1

    chunks = db_session.scalars(select(KnowledgeChunk)).all()
    assert len(chunks) == 1
    assert chunks[0].embedding
    assert chunks[0].token_count > 0

    search = client.post("/knowledge/search", headers=auth_headers(token), json={"query": "How much is Pro pricing?"})
    assert search.status_code == 200
    assert search.json()["results"][0]["filename"] == "pricing.txt"

    answer = client.post("/knowledge/ask", headers=auth_headers(token), json={"question": "How much is Pro pricing?"})
    assert answer.status_code == 200
    payload = answer.json()
    assert "pricing" in payload["answer"].lower()
    assert payload["citations"][0]["filename"] == "pricing.txt"


def test_knowledge_access_is_organization_scoped(client: TestClient) -> None:
    owner = register_user(client, email="rag-owner@example.com")
    other = register_user(client, email="rag-other@example.com")

    upload = client.post(
        "/knowledge/upload",
        headers=auth_headers(owner["access_token"]),
        files={"file": ("internal.txt", BytesIO(b"Private customer discount policy."), "text/plain")},
    )
    assert upload.status_code == 200

    documents = client.get("/knowledge/documents", headers=auth_headers(other["access_token"]))
    assert documents.status_code == 200
    assert documents.json() == []

    search = client.post("/knowledge/search", headers=auth_headers(other["access_token"]), json={"query": "discount policy"})
    assert search.status_code == 200
    assert search.json()["results"] == []


def test_invalid_upload_type_is_rejected(client: TestClient) -> None:
    token = register_user(client, email="bad-upload@example.com")["access_token"]

    response = client.post(
        "/knowledge/upload",
        headers=auth_headers(token),
        files={"file": ("script.exe", BytesIO(b"not allowed"), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Only PDF" in response.json()["detail"]
