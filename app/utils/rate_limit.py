
import asyncio
from collections import deque
from time import monotonic
from typing import Deque, Dict

from fastapi import HTTPException, status

_lock = asyncio.Lock()
_buckets: Dict[str, Deque[float]] = {}


async def check_rate_limit(
    bucket: str,
    identifier: str,
    *,
    limit: int,
    window_seconds: int,
):
    """
    Enforce a simple sliding-window rate limit for a given identifier.
    Raises HTTP 429 if the limit is exceeded.
    """

    key = f"{bucket}:{identifier}"
    now = monotonic()
    window_start = now - window_seconds

    async with _lock:
        timestamps = _buckets.get(key)
        if timestamps is None:
            timestamps = deque()
            _buckets[key] = timestamps

        while timestamps and timestamps[0] <= window_start:
            timestamps.popleft()

        if len(timestamps) >= limit:
            retry_after = max(1, int(window_seconds - (now - timestamps[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)
