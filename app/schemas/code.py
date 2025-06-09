from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.test_result import BaseTestResult

class TestResult(BaseTestResult):
    pass

class CodeSubmission(BaseModel):
    language: str = Field(..., pattern="^(python|java|cpp|javascript)$")
    code: str
    question_id: str

class CodeSubmissionResponse(BaseModel):
    submission_id: str
    status: str
    message: str
    results: Optional[List[TestResult]] = None
    total_passed: int
    total_tests: int
    execution_time: float
    memory_used: float
    error: bool = False
    success: bool = True
    input: Optional[str] = None
    expected_output: Optional[str] = None
    output_value: Optional[str] = None
    submitted_at: datetime

class SubmissionHistory(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    question_id: str
    language: str
    code: str
    status: str
    results: List[TestResult]
    submitted_at: datetime

    class Config:
        populate_by_name = True
