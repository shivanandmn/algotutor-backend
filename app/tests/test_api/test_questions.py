import pytest
from httpx import AsyncClient
from app.models.question import Question
from app.schemas.question import QuestionCreate

pytestmark = pytest.mark.asyncio

async def test_create_question(client: AsyncClient, admin_auth_headers):
    response = await client.post(
        "/api/v1/questions/",
        headers=admin_auth_headers,
        json={
            "title": "New Question",
            "content": "Write a function that multiplies two numbers",
            "level": "medium",
            "topics": ["math", "multiplication"],
            "code_snippets": [],
            "test_cases": [
                {
                    "input": "2 3",
                    "expected_output": "6",
                    "is_hidden": False
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Question"
    assert data["difficulty"] == "medium"
    assert len(data["test_cases"]) == 1

async def test_create_question_as_user(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/questions/",
        headers=auth_headers,
        json={
            "title": "New Question",
            "content": "Test",
            "level": "easy",
            "topics": ["test"],
            "code_snippets": [],
            "test_cases": []
        }
    )
    assert response.status_code == 403

async def test_list_questions(client: AsyncClient):
    response = await client.get("/api/v1/questions/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

async def test_list_questions_with_filters(client: AsyncClient, test_question):
    # Test difficulty filter
    response = await client.get("/api/v1/questions/?level=easy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(q["level"] == "easy" for q in data)

    # Test tags filter
    response = await client.get("/api/v1/questions/?topics=math")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all("math" in q["topics"] for q in data)

async def test_get_question(client: AsyncClient, test_question):
    question = await Question.find_one({"title": test_question["title"]})
    response = await client.get(f"/api/v1/questions/{question.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == test_question["title"]
    assert len(data["test_cases"]) == len(test_question["test_cases"])

async def test_update_question(client: AsyncClient, test_question, admin_auth_headers):
    question = await Question.find_one({"title": test_question["title"]})
    response = await client.put(
        f"/api/v1/questions/{question.id}",
        headers=admin_auth_headers,
        json={
            "title": "Updated Question",
            "content": test_question.content,
            "level": test_question.level,
            "topics": test_question.topics,
            "code_snippets": test_question.code_snippets,
            "test_cases": test_question["test_cases"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Question"

async def test_delete_question(client: AsyncClient, test_question, admin_auth_headers):
    question = await Question.find_one({"title": test_question["title"]})
    response = await client.delete(
        f"/api/v1/questions/{question.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    
    # Verify question is deleted
    question = await Question.find_one({"title": test_question["title"]})
    assert question is None
