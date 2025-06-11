from typing import Optional
from beanie import PydanticObjectId
from app.models.user import User

class DevAuthMiddleware:
    """Development authentication middleware that bypasses real authentication"""
    
    async def get_current_user(self, token: Optional[str] = None) -> User:
        """Returns a mock admin user for development"""
        return User(
            id=PydanticObjectId("000000000000000000000000"),  # Default ObjectId
            email="dev@example.com",
            name="Dev User",
            role="admin",
            google_id="dev_google_id"
        )

dev_auth_service = DevAuthMiddleware()
