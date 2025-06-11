from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.oauth2 import id_token
from google.auth.transport import requests
from jose import JWTError, jwt
from fastapi import HTTPException, status
from beanie import PydanticObjectId

from app.core.config import settings
from app.models.user import User

class AuthService:
    def __init__(self):
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRY_MINUTES

    async def verify_google_token(self, token: str) -> Dict[str, Any]:
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.google_client_id
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
                
            return {
                'email': idinfo['email'],
                'name': idinfo['name'],
                'google_id': idinfo['sub'],
                'picture': idinfo.get('picture')
            }
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )

    async def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        return encoded_jwt

    async def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    async def get_current_user(self, token: str) -> User:
        payload = await self.verify_token(token)
        google_id: str = payload.get("sub")
        
        if google_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
            
        user = await User.find_one({"google_id": google_id})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user

    async def authenticate_google(self, token: str) -> Dict[str, Any]:
        user_data = await self.verify_google_token(token)
        
        # Check if user exists
        user = await User.find_one({"google_id": user_data["google_id"]})
        
        if not user:
            # Create new user
            user = User(
                email=user_data["email"],
                name=user_data["name"],
                google_id=user_data["google_id"],
                picture=user_data.get("picture"),
                role="user",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            await user.insert()
        else:
            # Update existing user
            user.name = user_data["name"]
            user.picture = user_data.get("picture")
            user.updated_at = datetime.utcnow()
            await user.save()

        # Create access token
        access_token = await self.create_access_token(
            {"sub": user.google_id}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    async def update_user(self, user_id: PydanticObjectId, data: Dict[str, Any]) -> User:
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Update allowed fields
        allowed_fields = ["name", "picture"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        update_data["updated_at"] = datetime.utcnow()
        
        await user.update({"$set": update_data})
        return user

    async def update_user_role(
        self,
        user_id: PydanticObjectId,
        new_role: str,
        current_user: User
    ) -> User:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
            
        if new_role not in ["user", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role"
            )
            
        user = await User.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        user.role = new_role
        user.updated_at = datetime.utcnow()
        await user.save()
        
        return user
