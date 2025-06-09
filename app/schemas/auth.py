from pydantic import BaseModel, EmailStr
from typing import Optional

class TokenSchema(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None

class UserList(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    avatar: Optional[str] = None
