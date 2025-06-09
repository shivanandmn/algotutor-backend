from datetime import datetime
from beanie import Document, Link
from pydantic import Field

from app.models.question import Question
from app.models.user import User

class Solution(Document):
    question: Link[Question]
    user: Link[User]
    lang: str
    lang_slug: str
    code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "solutions"
