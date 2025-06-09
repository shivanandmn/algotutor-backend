from typing import Optional
from beanie import Document
from pydantic import BaseModel

class BaseTestResult(BaseModel):
    test_case_id: str
    passed: bool
    execution_time: float  # in milliseconds
    memory_used: float    # in MB
    output: Optional[str] = None
    error: Optional[str] = None

class TestResult(BaseTestResult, Document):
    is_hidden: bool = False
