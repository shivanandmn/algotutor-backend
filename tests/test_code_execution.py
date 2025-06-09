import pytest
from app.services.code_service import CodeExecutionService
from app.schemas.question import Question, TestCase, CodeSnippet, Language

@pytest.fixture
def code_service():
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
