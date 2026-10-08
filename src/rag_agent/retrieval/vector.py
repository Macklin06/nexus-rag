from collections.abc import Sequence

from sqlalchemy import Select, func, select

from rag_agent.db.models import DocumentChunk


def build_full_text_search_query(
    query: str,
    top_k: int = 5,
) -> Select:
    if not query.strip():
        raise ValueError("query must not be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    search_vector = func.to_tsvector("simple", DocumentChunk.content)
    search_query = func.plainto_tsquery("simple", query)
    rank = func.ts_rank_cd(search_vector, search_query).label("rank")

    return (
        select(DocumentChunk, rank)
        .where(search_vector.op("@@")(search_query))
        .order_by(rank.desc())
        .limit(top_k)
    )


def build_vector_search_query(
    query_embedding: Sequence[float],
    top_k: int = 5,
) -> Select:
    if not query_embedding:
        raise ValueError("query_embedding must not be empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
        "distance"
    )

    return (
        select(DocumentChunk, distance)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(top_k)
    )


def reciprocal_rank_fusion(
    ranked_lists: list[list[int]],
    k: int = 60,
) -> list[tuple[int, float]]:
    if k <= 0:
        raise ValueError("k must be greater than 0")

    scores: dict[int, float] = {}

    for ranked_list in ranked_lists:
        for rank, chunk_id in enumerate(ranked_list, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    return sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )