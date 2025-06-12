from typing import Optional, List, Any
from app.models.user import User
from app.core.config import settings

class MockAuthService:
    async def get_current_user(self, token: Optional[str] = None) -> User:
        # Return a mock admin user
        return User(
            email="mock@admin.com",
            full_name="Mock Admin",
            role="admin",
            is_active=True,
            is_superuser=True
        )
    
    def create_access_token(self, user: User) -> str:
        return "mock_token"
    
    async def update_user(self, user_id: str, user_update: Any) -> User:
        return await self.get_current_user()
    
    async def get_users(self, skip: int = 0, limit: int = 10) -> List[User]:
        return [await self.get_current_user()]
    
    async def update_user_role(self, user_id: str, role: str) -> User:
        mock_user = await self.get_current_user()
        mock_user.role = role
        return mock_user

mock_auth_service = MockAuthService()
