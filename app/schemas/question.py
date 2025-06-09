from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, constr
from enum import Enum

class Language(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    CPP = "cpp"
    JAVASCRIPT = "javascript"

class TestCase(BaseModel):
    input: str
    expected_output: str
    timeout_ms: int = 2000
    memory_limit_mb: int = 512
    is_hidden: bool = False

class CodeSnippet(BaseModel):
    language: Language
    code: str
    template: bool = False
    is_starter_code: bool = False

class QuestionBase(BaseModel):
    level: str = Field(..., pattern="^(easy|medium|hard)$")
    topics: List[str]
    companies: Optional[List[str]] = Field(default_factory=list)
    title: str
    title_slug: str = ""
    likes: int = 0
    dislikes: int = 0
    content: str
    code_snippets: List[CodeSnippet]
    test_cases: List[TestCase]
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    hints: List[str] = Field(default_factory=list)
    solution_explanation: Optional[str] = None
    acceptance_rate: float = 0.0
    submission_count: int = 0
    success_count: int = 0

class QuestionCreate(QuestionBase):
    pass

class QuestionUpdate(QuestionBase):
    pass

class Question(QuestionBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        populate_by_name = True
