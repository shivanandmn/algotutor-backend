from typing import Optional
from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime

class User(Document):
    email: EmailStr
    name: str
    role: str = Field(default="user")
    google_id: str = Field(unique=True)
    image: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            "email",
            "google_id",
        ]

    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "role": "user",
                "google_id": "123456789",
                "image": "https://example.com/image.jpg",
                "profile_image_url": "https://example.com/profile.jpg"
            }
        }
