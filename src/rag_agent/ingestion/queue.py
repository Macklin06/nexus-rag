import redis

from rag_agent.ingestion.jobs import IngestionJob


class IngestionQueue:
    QUEUE_NAME = "document_ingestion"

    def __init__(self, client: redis.Redis):
        self.client = client

    def enqueue(self, job: IngestionJob) -> None:
        self.client.rpush(
            self.QUEUE_NAME,
            job.to_payload(),
        )

    def dequeue(self, timeout: int = 5) -> IngestionJob | None:
        result = self.client.blpop(
            self.QUEUE_NAME,
            timeout=timeout,
        )

        if result is None:
            return None

        _, payload = result

        return IngestionJob.from_payload(payload)