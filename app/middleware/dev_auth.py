from typing import Optional
from app.models.user import User

class DevAuthMiddleware:
    """Development authentication middleware that bypasses real authentication"""
    
    async def get_current_user(self, token: Optional[str] = None) -> User:
        """Returns a mock admin user for development"""
        return User(
            id="dev_user_id",
            email="dev@example.com",
            username="dev_user",
            role="admin",
            is_active=True
        )

dev_auth_service = DevAuthMiddleware()
