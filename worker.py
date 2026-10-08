import os
import time

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rag_agent.ingestion.queue import IngestionQueue
from rag_agent.ingestion.processor import process_document_version


DATABASE_URL = os.environ["DATABASE_URL"]

redis_client = redis.Redis.from_url(
    os.environ["REDIS_URL"],
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=None,
)

ingestion_queue = IngestionQueue(redis_client)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


print(
    "Worker started. Waiting for ingestion jobs...",
    flush=True,
)


while True:
    try:
        job = ingestion_queue.dequeue(timeout=5)

        if job is None:
            continue

        print(
            f"Received ingestion job for document version "
            f"{job.document_version_id}",
            flush=True,
        )

        with Session(engine) as db:
            process_document_version(
                db,
                job.document_version_id,
            )

        print(
            f"Completed ingestion job for document version "
            f"{job.document_version_id}",
            flush=True,
        )

    except redis.RedisError as exc:
        print(
            f"Redis connection error: {exc}. Retrying...",
            flush=True,
        )
        time.sleep(2)

    except Exception as exc:
        print(
            f"Worker error: {exc}",
            flush=True,
        )