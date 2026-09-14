import pytest
from pydantic import ValidationError

from rag_agent.models import Document, DocumentModel
from rag_agent.core import (
    DocumentNotFoundError,
    document_ids,
    timing,
)


def test_dataclass_creation():
    doc = Document(
        id=1,
        title="Mine Safety Guidelines",
        source="DGMS",
    )

    assert doc.id == 1
    assert doc.title == "Mine Safety Guidelines"
    assert doc.source == "DGMS"


def test_pydantic_validation():
    with pytest.raises(ValidationError):
        DocumentModel(
            id="hello",
            title="Mine Safety Guidelines",
            source="DGMS",
        )


def test_custom_exception():
    with pytest.raises(DocumentNotFoundError):
        raise DocumentNotFoundError("Document not found")


def test_generator():
    result = list(document_ids())

    assert result == [0, 1, 2, 3, 4]


def test_timing_preserves_return_value():

    @timing
    def add(a, b):
        return a + b

    result = add(2, 3)

    assert result == 5

