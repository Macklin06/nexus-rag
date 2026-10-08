from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rag_agent.db.database import Base
from rag_agent.db.models import (
    Document,
    DocumentChunk,
    DocumentVersion,
    IngestionStatus,
)
from rag_agent.ingestion.processor import process_document_version


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    return Session(engine)


def test_process_document_version_creates_chunks():
    db = make_session()

    document = Document(
        title="Test",
        content="abcdefghij",
        source="test",
        content_hash="hash",
        current_version=1,
    )
    db.add(document)
    db.flush()

    version = DocumentVersion(
        document_id=document.id,
        version=1,
        content="abcdefghij",
        content_hash="hash",
    )
    db.add(version)
    db.commit()

    process_document_version(db, version.id)

    db.refresh(version)

    assert version.ingestion_status == IngestionStatus.COMPLETED
    assert len(version.chunks) == 1
    assert version.chunks[0].content == "abcdefghij"
    assert version.chunks[0].chunk_index == 0


def test_processing_is_idempotent_for_completed_version():
    db = make_session()

    document = Document(
        title="Test",
        content="abcdefghij",
        source="test",
        content_hash="hash",
        current_version=1,
    )
    db.add(document)
    db.flush()

    version = DocumentVersion(
        document_id=document.id,
        version=1,
        content="abcdefghij",
        content_hash="hash",
        ingestion_status=IngestionStatus.COMPLETED,
    )
    db.add(version)
    db.commit()

    process_document_version(db, version.id)

    db.refresh(version)

    assert version.ingestion_status == IngestionStatus.COMPLETED
    assert version.chunks == []


def test_chunks_belong_to_the_version_not_document():
    db = make_session()

    document = Document(
        title="Test",
        content="version one",
        source="test",
        content_hash="hash1",
        current_version=2,
    )
    db.add(document)
    db.flush()

    version_one = DocumentVersion(
        document_id=document.id,
        version=1,
        content="version one",
        content_hash="hash1",
    )

    version_two = DocumentVersion(
        document_id=document.id,
        version=2,
        content="version two",
        content_hash="hash2",
    )

    db.add_all([version_one, version_two])
    db.commit()

    process_document_version(db, version_one.id)
    process_document_version(db, version_two.id)

    db.refresh(version_one)
    db.refresh(version_two)

    assert all(
        chunk.document_version_id == version_one.id
        for chunk in version_one.chunks
    )

    assert all(
        chunk.document_version_id == version_two.id
        for chunk in version_two.chunks
    )