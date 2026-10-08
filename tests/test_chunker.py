import pytest

from rag_agent.ingestion.chunker import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_short_text_returns_one_chunk():
    chunks = chunk_text(
        "This is a short document.",
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].content == "This is a short document."


def test_long_text_creates_ordered_chunks():
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = chunk_text(
        text,
        chunk_size=10,
        chunk_overlap=2,
    )

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))

    assert chunks[0].content == "abcdefghij"
    assert chunks[1].content == "ijklmnopqr"
    assert chunks[2].content == "qrstuvwxyz"


def test_chunks_have_expected_overlap():
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = chunk_text(
        text,
        chunk_size=10,
        chunk_overlap=3,
    )

    for previous, current in zip(chunks, chunks[1:]):
        assert previous.content[-3:] == current.content[:3]


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=0)


def test_negative_overlap():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=10, chunk_overlap=-1)


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=10, chunk_overlap=10)