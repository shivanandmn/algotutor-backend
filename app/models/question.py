from datetime import datetime
from typing import List, Optional
from beanie import Document, Link
from pydantic import Field

from app.models.user import User
from app.schemas.question import QuestionBase

class Question(QuestionBase, Document):
    created_by: Link[User]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "questions"
        use_state_management = True

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
