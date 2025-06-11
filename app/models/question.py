from datetime import datetime
from typing import List, Optional
from beanie import Document, Link, PydanticObjectId
from pydantic import Field

from app.models.user import User
from app.schemas.question import QuestionBase, TestCase

class Question(QuestionBase, Document):
    # Convert test_cases to have proper string types
    test_cases: List[TestCase] = Field(default_factory=list)
    
    # Handle created_by as PydanticObjectId
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "questions"
        use_state_management = True

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: str
        }
