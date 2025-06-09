import asyncio
from datetime import datetime
from typing import AsyncGenerator, Dict

import pytest
from beanie import init_beanie
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.main import app
from app.models.code_submission import CodeSubmission, TestResult
from app.models.question import Question
from app.schemas.question import CodeSnippet, TestCase
from app.models.user import User
from app.services.auth_service import AuthService

@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    test_db_name = f"test_{settings.DATABASE_NAME}"
    test_db_url = settings.MONGODB_URL.replace(settings.DATABASE_NAME, test_db_name)
    motor_client = AsyncIOMotorClient(test_db_url)
    db = motor_client[test_db_name]

    print(f"DEBUG: Initializing Beanie with DB: {db.name} at {datetime.utcnow()}")
    document_models = [User, Question, CodeSubmission, TestResult]
    await init_beanie(
        database=db,
        document_models=document_models
    )
    print(f"DEBUG: Beanie initialized at {datetime.utcnow()}.")

    # Test User creation immediately after init_beanie
    try:
        print(f"DEBUG: Attempting to create a dummy User in setup_db at {datetime.utcnow()}.")
        dummy_user_data = {"email": "dummy@example.com", "name": "Dummy", "google_id": "dummy123", "role": "user"}
        dummy_user = User(**dummy_user_data)
        await dummy_user.insert()
        print(f"DEBUG: Dummy User created and inserted in setup_db: {dummy_user.id} at {datetime.utcnow()}.")
        await dummy_user.delete()
        print(f"DEBUG: Dummy User deleted in setup_db at {datetime.utcnow()}.")
    except Exception as e:
        print(f"DEBUG: Error creating dummy User in setup_db: {type(e).__name__} - {e} at {datetime.utcnow()}.")
        raise

    # Clear all collections before tests run
    print(f"DEBUG: Clearing collections before yield at {datetime.utcnow()}.")
    for model in document_models:
        await model.delete_all()
    print(f"DEBUG: Collections cleared at {datetime.utcnow()}.")
    
    yield
    
    # Cleanup after tests
    print(f"DEBUG: Cleaning up DB: {db.name} after yield at {datetime.utcnow()}.")
    # No need to delete_all again for function scope if cleared before yield
    await motor_client.drop_database(test_db_name)
    print(f"DEBUG: Dropped DB: {db.name} at {datetime.utcnow()}.")
    await motor_client.close()
    print(f"DEBUG: Motor client closed at {datetime.utcnow()}.")

@pytest.fixture
async def client(setup_db):
    async with AsyncClient(app=app, base_url="http://test", lifespan="off") as ac:
        yield ac

@pytest.fixture
async def test_user(setup_db) -> User:
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "google_id": "test123",
        "role": "user"
    }
    user = User(**user_data)
    await user.insert()
    return user

@pytest.fixture
async def test_admin(setup_db) -> User:
    admin_data = {
        "email": "admin@example.com",
        "name": "Admin User",
        "google_id": "admin123",
        "role": "admin"
    }
    admin = User(**admin_data)
    await admin.insert()
    return admin

@pytest.fixture
async def auth_headers(test_user) -> Dict[str, str]:
    user = await test_user
    auth_service = AuthService()
    token = await auth_service.create_access_token({"sub": str(user.google_id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def admin_auth_headers(test_admin) -> Dict[str, str]:
    admin = await test_admin
    auth_service = AuthService()
    token = await auth_service.create_access_token({"sub": str(admin.google_id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def test_question(test_admin) -> Question:
    question_data = {
        "title": "Test Question",
        "content": "Write a function that adds two numbers",
        "level": "easy",
        "topics": ["arrays", "math"],
        "code_snippets": [
            CodeSnippet(
                language="python",
                code="def add(a, b):\n    pass",
                is_solution=False,
                is_hidden=True
            )
        ],
        "test_cases": [
            TestCase(
                input="1 2",
                expected_output="3",
                timeout_ms=2000,
                memory_limit_mb=128,
                is_hidden=True
            )
        ],
        "created_by": test_admin
    }
    question = Question(**question_data)
    await question.insert()
    return question
