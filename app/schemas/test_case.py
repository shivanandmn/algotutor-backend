from typing import Optional, List
from pydantic import BaseModel

class TestCase(BaseModel):
    input: str
    expected_output: str
    is_hidden: bool = False
    score: float = 1.0
    description: Optional[str] = None

class TestResult(BaseModel):
    test_case_id: str
    passed: bool
    execution_time: float  # in milliseconds
    memory_used: float    # in MB
    output: Optional[str] = None
    error: Optional[str] = None
    is_hidden: bool = False

class TestSuite(BaseModel):
    test_cases: List[TestCase]
    time_limit: float = 2.0  # seconds
    memory_limit: float = 256.0  # MB
    score_to_pass: float = 1.0  # minimum score to pass
