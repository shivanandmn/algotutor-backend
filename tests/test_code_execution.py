import pytest
from app.services.code_service import CodeExecutionService
from app.schemas.question import Question, TestCase, CodeSnippet, Language

@pytest.fixture
def code_service(monkeypatch):
    # Mock Judge0 API responses
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
        
        def json(self):
            return self.json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")
    
    def mock_post(*args, **kwargs):
        return MockResponse({"token": "test-token"})
    
    def mock_get(*args, **kwargs):
        if "test-token" in args[0]:
            return MockResponse({
                "status": {"id": 3},  # Accepted
                "stdout": "[0,1]\n",
                "stderr": "",
                "compile_output": ""
            })
        return MockResponse({}, 404)
    
    # Apply mocks
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    monkeypatch.setattr(requests, "get", mock_get)
    
    return CodeExecutionService()

@pytest.fixture
def sample_question():
    # Sample "Two Sum" question
    return Question(
        id="test_id",
        title="Two Sum",
        level="easy",
        topics=["arrays", "hash-table"],
        content="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        code_snippets=[
            CodeSnippet(
                language=Language.PYTHON,
                code="def two_sum(nums, target):\n    # Your code here\n    pass",
                is_starter_code=True
            )
        ],
        test_cases=[
            TestCase(
                input="[2,7,11,15]\n9",
                expected_output="[0,1]",
                is_hidden=False
            ),
            TestCase(
                input="[3,2,4]\n6",
                expected_output="[1,2]",
                is_hidden=False
            ),
            TestCase(
                input="[3,3]\n6",
                expected_output="[0,1]",
                is_hidden=True
            )
        ],
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        created_by="test_user"
    )

async def test_python_code_execution(code_service, sample_question):
    # Correct solution
    code = """
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Read input
import json
nums = json.loads(input().strip())
target = int(input().strip())

# Execute and print result
result = two_sum(nums, target)
print(json.dumps(result))
"""
    
    # Test with the first test case
    test_case = sample_question.test_cases[0]
    result = await code_service.execute_code(
        code=code,
        lang="python",
        input_data=test_case.input
    )
    
    assert result["status"] == "success"
    assert result["output"].strip() == test_case.expected_output

async def test_invalid_python_code(code_service, sample_question):
    # Code with syntax error
    code = """
def two_sum(nums, target)
    return []  # Missing colon
"""
    
    test_case = sample_question.test_cases[0]
    result = await code_service.execute_code(
        code=code,
        lang="python",
        input_data=test_case.input
    )
    
    assert result["status"] == "error"
    assert "SyntaxError" in result["error"]
