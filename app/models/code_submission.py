from datetime import datetime
from typing import List, Optional
from beanie import Document, Link
from pydantic import Field

from app.models.user import User
from app.models.question import Question

class TestResult(Document):
    test_case_id: str
    passed: bool
    execution_time: float  # in milliseconds
    memory_used: float    # in MB
    output: Optional[str] = None
    error: Optional[str] = None
    is_hidden: bool = False

class CodeSubmission(Document):
    user: Link[User]
    question: Link[Question]
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
