from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def setup_cors(app):
    """Configure CORS middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Process-Time",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset"
        ]
    )
