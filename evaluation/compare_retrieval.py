import json
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rag_agent.ingestion.embeddings import embed_text
from rag_agent.retrieval.vector import (
    build_full_text_search_query,
    build_vector_search_query,
    reciprocal_rank_fusion,
)

load_dotenv(dotenv_path=".env")

engine = create_engine(os.environ["DATABASE_URL"])

TARGET_CASES = {
    "ATTN-01",
    "ATTN-03",
    "RAG-01",
}


def main() -> None:
    with open("evaluation/golden_set.json", encoding="utf-8") as file:
        cases = json.load(file)["cases"]

    selected = [
        case for case in cases
        if case["id"] in TARGET_CASES
    ]

    with Session(engine) as db:
        for case in selected:
            print("\n" + "=" * 100)
            print(case["id"])
            print(case["question"])
            print("=" * 100)

            embedding = embed_text(case["question"])

            vector_rows = db.execute(
                build_vector_search_query(
                    query_embedding=embedding,
                    top_k=5,
                )
            ).all()

            fts_rows = db.execute(
                build_full_text_search_query(
                    query=case["question"],
                    top_k=5,
                )
            ).all()

            vector_ids = [
                chunk.id
                for chunk, _ in vector_rows
            ]

            fts_ids = [
                chunk.id
                for chunk, _ in fts_rows
            ]

            hybrid = reciprocal_rank_fusion(
                [vector_ids, fts_ids]
            )[:5]

            print("\nVECTOR")
            print(vector_ids)

            print("\nFTS")
            print(fts_ids)

            print("\nHYBRID / RRF")
            print([chunk_id for chunk_id, _ in hybrid])


if __name__ == "__main__":
    main()