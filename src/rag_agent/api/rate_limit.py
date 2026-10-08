import time

import redis


class RateLimiter:
    def __init__(
        self,
        client: redis.Redis,
        limit: int = 60,
        window: int = 60,
    ):
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if window <= 0:
            raise ValueError("window must be greater than 0")

        self.client = client
        self.limit = limit
        self.window = window

    def allow(self, identifier: str) -> bool:
        now = int(time.time())
        window_id = now // self.window

        key = f"rate_limit:{identifier}:{window_id}"

        count = self.client.incr(key)

        if count == 1:
            self.client.expire(key, self.window)

        return count <= self.limit