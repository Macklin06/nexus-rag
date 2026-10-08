import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rag_agent.ingestion.embeddings import embed_text
from rag_agent.retrieval.vector import build_vector_search_query

load_dotenv()

engine = create_engine(
    os.environ["DATABASE_URL"],
    pool_pre_ping=True,
)

query_embedding = embed_text(
    "How does Nexus-RAG store document chunks?"
)

query = build_vector_search_query(
    query_embedding=query_embedding,
    top_k=5,
)

with Session(engine) as db:
    results = db.execute(query).all()

    for chunk, distance in results:
        similarity = 1 - distance

        print(
            f"id={chunk.id} "
            f"chunk_index={chunk.chunk_index} "
            f"distance={distance:.4f} "
            f"similarity={similarity:.4f} "
            f"content={chunk.content[:100]!r}"
        )