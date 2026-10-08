from sqlalchemy import delete
from sqlalchemy.orm import Session
from rag_agent.ingestion.embeddings import embed_text

from rag_agent.db.models import (
    DocumentChunk,
    DocumentVersion,
    IngestionStatus,
)
from rag_agent.ingestion.chunker import chunk_text


def process_document_version(
    db: Session,
    document_version_id: int,
) -> None:
    version = db.get(DocumentVersion, document_version_id)

    if version is None:
        raise ValueError(
            f"DocumentVersion {document_version_id} not found"
        )

    if version.ingestion_status == IngestionStatus.COMPLETED:
        return

    version.ingestion_status = IngestionStatus.PROCESSING
    db.commit()

    try:
        chunks = chunk_text(version.content)

        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_version_id == version.id
            )
        )

        for chunk in chunks:
            embedding = embed_text(chunk.content)

            db.add(
                DocumentChunk(
                    document_version_id=version.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    embedding=embedding,
                )
            )

        version.ingestion_status = IngestionStatus.COMPLETED
        db.commit()

    except Exception:
        db.rollback()

        version = db.get(DocumentVersion, document_version_id)

        if version is not None:
            version.ingestion_status = IngestionStatus.FAILED
            db.commit()

        raise