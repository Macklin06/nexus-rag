from rag_agent.ingestion.hashing import content_hash, normalize_content


def test_same_content_produces_same_hash():
    content = "Mine safety guidelines"

    assert content_hash(content) == content_hash(content)


def test_different_content_produces_different_hash():
    assert content_hash("Document A") != content_hash("Document B")


def test_hash_uses_utf8_content():
    content = "Mining sécurité"

    assert len(content_hash(content)) == 64


def test_outer_whitespace_is_normalized():
    assert content_hash("  hello world  ") == content_hash("hello world")


def test_internal_content_is_not_modified():
    assert normalize_content("hello  world") == "hello  world"