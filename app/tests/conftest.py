import pytest
from typing import AsyncGenerator, Dict
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime

from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.question import Question
from app.models.code_submission import CodeSubmission, TestResult
from app.services.auth_service import AuthService

# Test database setup
@pytest.fixture(autouse=True)
async def setup_db() -> AsyncGenerator:
    # Use a test database
    test_db_name = f"test_{settings.DATABASE_NAME}"
    test_db_url = settings.MONGODB_URL.replace(
        settings.DATABASE_NAME,
        test_db_name
    )
    
    client = AsyncIOMotorClient(test_db_url)
    await init_beanie(
        database=client[test_db_name],
        document_models=[User, Question, CodeSubmission]
    )
    
    yield
    
    # Cleanup
    await client.drop_database(test_db_name)
    await client.close()

# Test client
@pytest.fixture
async def client() -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Auth fixtures
@pytest.fixture
async def test_user() -> Dict:
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "google_id": "test123",
        "role": "user"
    }
    user = User(**user_data)
    await user.insert()
    return user_data

@pytest.fixture
async def test_admin() -> Dict:
    admin_data = {
        "email": "admin@example.com",
        "name": "Admin User",
        "google_id": "admin123",
        "role": "admin"
    }
    admin = User(**admin_data)
    await admin.insert()
    return admin_data

@pytest.fixture
async def auth_headers(test_user) -> Dict:
    auth_service = AuthService()
    token = await auth_service.create_access_token({"sub": str(test_user["google_id"])})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_auth_headers(test_admin) -> Dict:
    auth_service = AuthService()
    token = await auth_service.create_access_token({"sub": str(test_admin["google_id"])})
    return {"Authorization": f"Bearer {token}"}

# Question fixtures
@pytest.fixture
async def test_question(test_admin) -> Dict:
    question_data = {
        "title": "Test Question",
        "description": "Write a function that adds two numbers",
        "difficulty": "easy",
        "tags": ["math", "basic"],
        "test_cases": [
            {
                "input": "1 2",
                "expected_output": "3",
                "is_hidden": False
            },
            {
                "input": "0 0",
                "expected_output": "0",
                "is_hidden": True
            }
        ],
        "created_by": str(test_admin["google_id"]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    question = Question(**question_data)
    await question.insert()
    return question_data

# Code submission fixtures
@pytest.fixture
def test_python_code() -> str:
    return """
def add(a, b):
    return a + b

a, b = map(int, input().split())
print(add(a, b))
"""

@pytest.fixture
def test_java_code() -> str:
    return """
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int a = scanner.nextInt();
        int b = scanner.nextInt();
        System.out.println(add(a, b));
    }
    
    public static int add(int a, int b) {
        return a + b;
    }
}
"""

@pytest.fixture
def test_cpp_code() -> str:
    return """
#include <iostream>
using namespace std;

int add(int a, int b) {
    return a + b;
}

int main() {
    int a, b;
    cin >> a >> b;
    cout << add(a, b) << endl;
    return 0;
}
"""
