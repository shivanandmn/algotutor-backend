from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time

class RateLimiter(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 100
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.clients: Dict[str, list] = {}

    def _get_client_identifier(self, request: Request) -> str:
        # Use forwarded IP if behind proxy, else remote address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup_old_requests(self, client_id: str):
        """Remove requests older than 1 minute"""
        if client_id in self.clients:
            current_time = time.time()
            self.clients[client_id] = [
                req_time for req_time in self.clients[client_id]
                if current_time - req_time < 60
            ]

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_identifier(request)
        current_time = time.time()

        # Initialize client's request history
        if client_id not in self.clients:
            self.clients[client_id] = []

        # Clean up old requests
        self._cleanup_old_requests(client_id)

        # Check burst limit
        if len(self.clients[client_id]) >= self.burst_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Burst rate limit exceeded"
            )

        # Check rate limit
        requests_last_minute = len(self.clients[client_id])
        if requests_last_minute >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Add current request
        self.clients[client_id].append(current_time)
        
        # Call next middleware/route handler
        response = await call_next(request)
        return response

        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.clients[client_id])
        reset_time = datetime.fromtimestamp(current_time + 60)

        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset_time.isoformat()
