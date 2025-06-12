from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

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
        client_id = None
        current_time = None
        
        try:
            # Skip rate limiting for health check and OPTIONS requests
            if request.url.path == "/health" or request.method == "OPTIONS":
                return await call_next(request)

            client_id = self._get_client_identifier(request)
            current_time = time.time()

            # Initialize client's request history if needed
            if client_id not in self.clients:
                self.clients[client_id] = []

            # Clean up old requests
            self._cleanup_old_requests(client_id)

            # Check burst limit
            if len(self.clients[client_id]) >= self.burst_limit:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Burst rate limit exceeded"}
                )
                self._add_rate_limit_headers(response, client_id, current_time)
                return response

            # Check rate limit
            requests_last_minute = len(self.clients[client_id])
            if requests_last_minute >= self.requests_per_minute:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"}
                )
                self._add_rate_limit_headers(response, client_id, current_time)
                return response

            # Add current request
            self.clients[client_id].append(current_time)
            
            # Call next middleware/route handler
            response = await call_next(request)
            
            # Add rate limit headers to successful response
            self._add_rate_limit_headers(response, client_id, current_time)
            return response
            
        except Exception as e:
            logging.error(f"Rate limiter error: {str(e)}")
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
            
            # Only add rate limit headers if we have the necessary info
            if client_id and current_time:
                try:
                    self._add_rate_limit_headers(response, client_id, current_time)
                except Exception as header_error:
                    logging.error(f"Failed to add rate limit headers: {str(header_error)}")
                    
            return response

    def _add_rate_limit_headers(self, response, client_id: str, current_time: float):
        """Helper method to add rate limit headers to a response"""
        try:
            remaining = max(0, self.requests_per_minute - len(self.clients.get(client_id, [])))
            reset_time = datetime.fromtimestamp(current_time + 60)
            
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = reset_time.isoformat()
        except Exception as e:
            logging.error(f"Error adding rate limit headers: {str(e)}")
