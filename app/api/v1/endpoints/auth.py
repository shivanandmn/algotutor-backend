from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from typing import List, Dict, Any
from beanie import PydanticObjectId
import httpx

from app.models.user import User
from app.schemas.auth import TokenSchema, UserUpdate, UserList
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import JWTBearer

router = APIRouter()
auth_service = AuthService()

@router.post("/login/google", response_model=TokenSchema)
async def google_login(token: Dict[str, str]):
    """Login or register user with Google OAuth token"""
    if not token.get("token"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
        
    try:
        # Verify token with Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token['token']}"},
                params={"personFields": "emailAddresses,names,photos"}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            google_data = response.json()
        
        # Find or create user
        user = await User.find_one({"google_id": google_data["sub"]})
        if not user:
            user = User(
                google_id=google_data["sub"],
                email=google_data["email"],
                name=google_data["name"],
                avatar=google_data["picture"],
                role="user"
            )
            await user.insert()
        
        # Generate JWT token
        access_token = auth_service.create_access_token(user)
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(auth_service.get_current_user)):
    """Logout current user"""
    try:
        # Clear JWT cookie if using cookie-based auth
        response.delete_cookie("Authorization")
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Update current user information"""
    try:
        updated_user = await auth_service.update_user(current_user.id, user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users", response_model=List[UserList])
async def list_users(
    current_user: User = Depends(auth_service.get_current_user),
    skip: int = 0,
    limit: int = 10
):
    """List all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    users = await auth_service.get_users(skip, limit)
    return users

@router.put("/users/{user_id}/role", response_model=User)
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Update user role (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    if role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )
    try:
        updated_user = await auth_service.update_user_role(user_id, role)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
