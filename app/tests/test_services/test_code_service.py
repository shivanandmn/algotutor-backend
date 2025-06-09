import pytest
import docker
from app.services.code_service import CodeExecutionService
from app.models.code_submission import CodeSubmission, TestResult

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def code_service():
    return CodeExecutionService()

async def test_execute_python_code(code_service, test_python_code):
    test_case = {
        "input": "1 2",
        "expected_output": "3",
        "is_hidden": False
    }
    
    result = await code_service.execute_code(
        code=test_python_code,
        language="python",
        test_case=test_case
    )
    
    assert result["success"] is True
    assert result["output"].strip() == "3"
    assert result["error"] is None

async def test_execute_java_code(code_service, test_java_code):
    test_case = {
        "input": "2 3",
        "expected_output": "5",
        "is_hidden": False
    }
    
    result = await code_service.execute_code(
        code=test_java_code,
        language="java",
        test_case=test_case
    )
    
    assert result["success"] is True
    assert result["output"].strip() == "5"
    assert result["error"] is None

async def test_execute_cpp_code(code_service, test_cpp_code):
    test_case = {
        "input": "4 5",
        "expected_output": "9",
        "is_hidden": False
    }
    
    result = await code_service.execute_code(
        code=test_cpp_code,
        language="cpp",
        test_case=test_case
    )
    
    assert result["success"] is True
    assert result["output"].strip() == "9"
    assert result["error"] is None

async def test_execute_invalid_code(code_service):
    test_case = {
        "input": "1 2",
        "expected_output": "3",
        "is_hidden": False
    }
    
    invalid_python_code = """
    def add(a, b):
        return a + # syntax error
    """
    
    result = await code_service.execute_code(
        code=invalid_python_code,
        language="python",
        test_case=test_case
    )
    
    assert result["success"] is False
    assert result["error"] is not None

async def test_execute_timeout_code(code_service):
    test_case = {
        "input": "1",
        "expected_output": "1",
        "is_hidden": False
    }
    
    infinite_loop_code = """
    while True:
        pass
    """
    
    result = await code_service.execute_code(
        code=infinite_loop_code,
        language="python",
        test_case=test_case
    )
    
    assert result["success"] is False
    assert "timeout" in result["error"].lower()

async def test_execute_memory_limit_code(code_service):
    test_case = {
        "input": "1",
        "expected_output": "1",
        "is_hidden": False
    }
    
    memory_heavy_code = """
    x = [0] * 1000000000  # Attempt to allocate too much memory
    """
    
    result = await code_service.execute_code(
        code=memory_heavy_code,
        language="python",
        test_case=test_case
    )
    
    assert result["success"] is False
    assert "memory" in result["error"].lower()
