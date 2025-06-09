import pytest
from httpx import AsyncClient
from app.models.question import Question

pytestmark = pytest.mark.asyncio

async def test_create_question(client: AsyncClient, admin_auth_headers):
    response = await client.post(
        "/api/v1/questions/",
        headers=admin_auth_headers,
        json={
            "title": "New Question",
            "description": "Write a function that multiplies two numbers",
            "difficulty": "medium",
            "tags": ["math", "multiplication"],
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
            "description": "Test",
            "difficulty": "easy",
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
    response = await client.get("/api/v1/questions/?difficulty=easy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(q["difficulty"] == "easy" for q in data)

    # Test tags filter
    response = await client.get("/api/v1/questions/?tags=math")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all("math" in q["tags"] for q in data)

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
            "description": test_question["description"],
            "difficulty": test_question["difficulty"],
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
