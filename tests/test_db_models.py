import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rag_agent.db.database import Base
from rag_agent.db.models import Document, DocumentChunk, DocumentVersion


@pytest.fixture
def database_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def make_version(document_id: int, version: int, content: str) -> DocumentVersion:
    return DocumentVersion(
        document_id=document_id,
        version=version,
        content=content,
        content_hash=f"hash-{version}",
    )


def test_chunks_are_ordered_under_document_version(database_session):
    document = Document(
        title="Mine Safety",
        content="Full document",
        source="DGMS",
        content_hash="document-hash",
        current_version=1,
    )
    version = make_version(document_id=1, version=1, content="Full document")
    version.chunks.extend(
        [
            DocumentChunk(chunk_index=1, content="second"),
            DocumentChunk(chunk_index=0, content="first"),
        ]
    )
    document.versions.append(version)

    database_session.add(document)
    database_session.commit()
    database_session.refresh(version)

    assert [chunk.chunk_index for chunk in version.chunks] == [0, 1]
    assert version.chunks[0].document_version is version


def test_duplicate_chunk_index_is_rejected_for_one_version(database_session):
    document = Document(
        title="Mine Safety",
        content="Full document",
        source="DGMS",
        content_hash="document-hash",
        current_version=1,
    )
    version = make_version(document_id=1, version=1, content="Full document")
    version.chunks.extend(
        [
            DocumentChunk(chunk_index=0, content="first"),
            DocumentChunk(chunk_index=0, content="duplicate"),
        ]
    )
    document.versions.append(version)
    database_session.add(document)

    with pytest.raises(IntegrityError):
        database_session.commit()


def test_same_chunk_index_is_allowed_for_different_versions(database_session):
    document = Document(
        title="Mine Safety",
        content="Full document",
        source="DGMS",
        content_hash="document-hash",
        current_version=2,
    )
    first_version = make_version(document_id=1, version=1, content="First")
    second_version = make_version(document_id=1, version=2, content="Second")
    first_version.chunks.append(DocumentChunk(chunk_index=0, content="first"))
    second_version.chunks.append(DocumentChunk(chunk_index=0, content="second"))
    document.versions.extend([first_version, second_version])
    database_session.add(document)

    database_session.commit()

    assert first_version.chunks[0].chunk_index == second_version.chunks[0].chunk_index
