import hashlib
import json

import redis


class QueryCache:
    KEY_PREFIX = "query_cache"

    def __init__(
        self,
        client: redis.Redis,
        ttl: int = 300,
    ):
        if ttl <= 0:
            raise ValueError("ttl must be greater than 0")

        self.client = client
        self.ttl = ttl

    def build_key(
        self,
        query: str,
        top_k: int,
    ) -> str:
        payload = json.dumps(
            {
                "query": query.strip(),
                "top_k": top_k,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

        return f"{self.KEY_PREFIX}:{digest}"

    def get(
        self,
        query: str,
        top_k: int,
    ) -> str | None:
        key = self.build_key(query, top_k)
        return self.client.get(key)

    def set(
        self,
        query: str,
        top_k: int,
        value: str,
    ) -> None:
        key = self.build_key(query, top_k)
        self.client.setex(
            key,
            self.ttl,
            value,
        )