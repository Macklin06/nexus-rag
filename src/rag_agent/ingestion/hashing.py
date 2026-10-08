# src/rag_agent/ingestion/hashing.py

import hashlib


def normalize_content(content: str) -> str:
    """Normalize document content before hashing."""
    return content.strip()


def content_hash(content: str) -> str:
    """Return the SHA-256 hash of normalized document content."""
    normalized = normalize_content(content)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()