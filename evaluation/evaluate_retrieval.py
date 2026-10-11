import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

BASE_URL = os.getenv("EVAL_API_URL", "http://localhost:8000")
API_KEY = os.environ["API_KEY"]
TOP_K = 5

GOLDEN_SET_PATH = Path(__file__).with_name("golden_set.json")
DATABASE_URL = os.environ["DATABASE_URL"]


def load_golden_set() -> dict:
    with GOLDEN_SET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_chunk_ids(cases: list[dict]) -> dict[str, set[int]]:
    engine = create_engine(DATABASE_URL)

    sql = text(
        """
        SELECT
            dc.id AS chunk_id,
            d.title,
            dc.chunk_index
        FROM document_chunks dc
        JOIN document_versions dv
            ON dv.id = dc.document_version_id
        JOIN documents d
            ON d.id = dv.document_id
        WHERE d.title = :document
          AND dc.chunk_index = :chunk_index
                    AND dv.version = d.current_version
        """
    )

    resolved = {}

    with engine.connect() as db:
        for case in cases:
            chunk_ids = set()

            for reference in case["evidence"]["acceptable_chunks"]:
                row = db.execute(
                    sql,
                    {
                        "document": reference["document"],
                        "chunk_index": reference["chunk_index"],
                    },
                ).mappings().first()

                if row is None:
                    raise RuntimeError(
                        f"Could not resolve benchmark chunk: "
                        f"{reference['document']} "
                        f"chunk_index={reference['chunk_index']}"
                    )

                chunk_ids.add(row["chunk_id"])

            resolved[case["id"]] = chunk_ids

    return resolved


def query_api(question: str, top_k: int) -> list[dict]:
    response = requests.post(
        f"{BASE_URL}/query",
        headers={
            "Content-Type": "application/json",
            "api-key": API_KEY,
        },
        json={
            "query": question,
            "top_k": top_k,
        },
        timeout=120,
    )

    response.raise_for_status()
    return response.json()["results"]


def evidence_recall_at_k(
    retrieved_ids: list[int],
    acceptable_ids: set[int],
) -> float:
    if not acceptable_ids:
        return 0.0

    return float(bool(set(retrieved_ids) & acceptable_ids))


def reciprocal_rank(
    retrieved_ids: list[int],
    acceptable_ids: set[int],
) -> float:
    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in acceptable_ids:
            return 1.0 / rank

    return 0.0


def main() -> None:
    golden_set = load_golden_set()
    cases = golden_set["cases"]

    resolved_chunks = resolve_chunk_ids(cases)

    results = []

    for case in cases:
        retrieved = query_api(case["question"], TOP_K)
        retrieved_ids = [item["chunk_id"] for item in retrieved]

        acceptable_ids = resolved_chunks[case["id"]]

        evidence_recall = evidence_recall_at_k(
            retrieved_ids,
            acceptable_ids=acceptable_ids,
        )

        mrr = reciprocal_rank(
            retrieved_ids,
            acceptable_ids,
        )

        result = {
            "id": case["id"],
            "question": case["question"],
            "acceptable_chunk_ids": sorted(acceptable_ids),
            "retrieved_chunk_ids": retrieved_ids,
            "evidence_recall_at_5": evidence_recall,
            "reciprocal_rank": mrr,
        }

        results.append(result)

        print(
            f"\n{case['id']}: "
            f"EvidenceRecall@5={evidence_recall:.3f} "
            f"RR={mrr:.3f}"
        )

        print(f"  Acceptable chunk IDs: {sorted(acceptable_ids)}")

        for rank, item in enumerate(retrieved, start=1):
            print(
                f"  #{rank}: "
                f"chunk_id={item['chunk_id']} "
                f"version={item['document_version_id']} "
                f"index={item['chunk_index']} "
                f"rrf={item['rrf_score']:.6f}"
            )

    mean_recall = sum(
        result["evidence_recall_at_5"] for result in results
    ) / len(results)

    mean_mrr = sum(
        result["reciprocal_rank"] for result in results
    ) / len(results)

    print()
    print(f"Cases: {len(results)}")
    print(f"Evidence Recall@5: {mean_recall:.3f}")
    print(f"MRR@5:    {mean_mrr:.3f}")


if __name__ == "__main__":
    main()