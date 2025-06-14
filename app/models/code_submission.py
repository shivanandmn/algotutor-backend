from datetime import datetime
from typing import List, Optional
from beanie import Document, Link
from pydantic import Field
from pydantic.typing import Annotated
from app.models.user import User
from app.models.question import Question
from app.models.test_result import TestResult
from beanie import PydanticObjectId

class CodeSubmission(Document):

    class Settings:
        arbitrary_types_allowed = True
        name = "code_submissions"
        indexes = [
            "user",
            "question",
            "status",
            "submitted_at"
        ]

    user: Annotated[PydanticObjectId, Link[User]]
    question: Annotated[PydanticObjectId, Link[Question]]
    language: str
    code: str
    status: str = Field(
        default="pending",
        description="pending, running, completed, error"
    )
    results: List[TestResult] = []
    total_passed: int = 0
    total_tests: int = 0
    execution_time: float = 0  # Total execution time
    memory_used: float = 0     # Peak memory usage
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Settings:
        name = "code_submissions"
        indexes = [
            "user",
            "question",
            "status",
            "submitted_at"
        ]
