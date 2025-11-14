"""Rate limiting middleware using Redis"""

import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket rate limiting middleware"""

    def __init__(self, app, redis_client: redis.Redis = None):
        super().__init__(app)
        self.redis_client = redis_client
        self.enabled = settings.rate_limit_enabled

    async def dispatch(self, request: Request, call_next):
        if not self.enabled or not self.redis_client:
            return await call_next(request)

        # Get user identifier (IP or user ID)
        user_id = getattr(request.state, "user_id", None)
        client_ip = request.client.host if request.client else "unknown"
        identifier = user_id or client_ip

        # Check rate limit
        allowed = await self._check_rate_limit(identifier)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )

        response = await call_next(request)
        return response

    async def _check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit using token bucket algorithm"""
        now = time.time()
        key_minute = f"rate_limit:minute:{identifier}"
        key_hour = f"rate_limit:hour:{identifier}"

        # Check minute limit
        minute_count = await self.redis_client.incr(key_minute)
        if minute_count == 1:
            await self.redis_client.expire(key_minute, 60)

        if minute_count > settings.rate_limit_per_minute:
            return False

        # Check hour limit
        hour_count = await self.redis_client.incr(key_hour)
        if hour_count == 1:
            await self.redis_client.expire(key_hour, 3600)

        if hour_count > settings.rate_limit_per_hour:
            return False

        return True
