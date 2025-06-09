from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import AuthService

class JWTBearer(HTTPBearer):
    def __init__(
        self,
        auto_error: bool = True,
        admin_required: bool = False
    ):
        super().__init__(auto_error=auto_error)
        self.admin_required = admin_required
        self.auth_service = AuthService()

    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code"
            )
            
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication scheme"
            )
            
        user = await self.auth_service.get_current_user(credentials.credentials)
        
        if self.admin_required and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
            
        # Attach user to request state
        request.state.user = user
        return credentials
