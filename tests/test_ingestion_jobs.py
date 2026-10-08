import pytest

from rag_agent.ingestion.jobs import IngestionJob


def test_job_serializes_document_version_id():
    job = IngestionJob(document_version_id=42)

    assert job.to_payload() == "42"


def test_job_deserializes_document_version_id():
    job = IngestionJob.from_payload("42")

    assert job.document_version_id == 42


def test_job_rejects_invalid_payload():
    with pytest.raises(ValueError):
        IngestionJob.from_payload("abc")


def test_job_rejects_non_positive_id():
    with pytest.raises(ValueError):
        IngestionJob.from_payload("0")