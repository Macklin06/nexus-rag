import os

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])

SEARCHES = {
    "attention": [
        "multi-head attention",
        "self-attention",
        "scaled dot-product attention",
        "positional encoding",
        "encoder decoder",
    ],
    "rag": [
        "retrieval-augmented generation",
        "retriever",
        "non-parametric memory",
        "parametric memory",
        "dense vector",
    ],
    "lora": [
        "low-rank adaptation",
        "trainable parameters",
        "rank",
        "fine-tuning",
        "LoRA",
    ],
    "react": [
        "ReAct",
        "reasoning",
        "acting",
        "tool",
        "action space",
    ],
}


def main() -> None:
    sql = text(
        """
        SELECT
            d.title,
            dc.id AS chunk_id,
            dc.document_version_id,
            dc.chunk_index,
            dc.content
        FROM document_chunks dc
        JOIN document_versions dv
            ON dv.id = dc.document_version_id
        JOIN documents d
            ON d.id = dv.document_id
        WHERE d.id IN (53, 54, 55, 56)
          AND dc.content ILIKE :pattern
        ORDER BY d.id, dc.chunk_index
        """
    )

    with engine.connect() as db:
        for category, terms in SEARCHES.items():
            print(f"\n{'=' * 80}")
            print(f"CATEGORY: {category}")
            print(f"{'=' * 80}")

            seen = set()

            for term in terms:
                rows = db.execute(
                    sql,
                    {"pattern": f"%{term}%"},
                ).mappings()

                for row in rows:
                    if row["chunk_id"] in seen:
                        continue

                    seen.add(row["chunk_id"])

                    print(
                        f"\n[{row['title']}] "
                        f"chunk_id={row['chunk_id']} "
                        f"chunk_index={row['chunk_index']}"
                    )
                    print(row["content"][:1200])


if __name__ == "__main__":
    main()