import pytest
from httpx import AsyncClient
from app.models.code_submission import CodeSubmission
from app.models.question import Question

pytestmark = pytest.mark.asyncio

async def test_submit_code(
    client: AsyncClient,
    auth_headers,
    test_question,
    test_python_code
):
    response = await client.post(
        "/api/v1/code/submit",
        headers=auth_headers,
        json={
            "language": "python",
            "code": test_python_code,
            "question_id": str(test_question.id)
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "submission_id" in data
    assert data["status"] == "queued"

async def test_submit_invalid_language(
    client: AsyncClient,
    auth_headers,
    test_question
):
    response = await client.post(
        "/api/v1/code/submit",
        headers=auth_headers,
        json={
            "language": "invalid",
            "code": "print('test')",
            "question_id": str(test_question.id)
        }
    )
    assert response.status_code == 400

async def test_get_submission_status(
    client: AsyncClient,
    auth_headers,
    test_question,
    test_python_code
):
    # First submit code
    submit_response = await client.post(
        "/api/v1/code/submit",
        headers=auth_headers,
        json={
            "language": "python",
            "code": test_python_code,
            "question_id": str(test_question.id)
        }
    )
    submission_id = submit_response.json()["submission_id"]
    
    # Then check status
    response = await client.get(
        f"/api/v1/code/status/{submission_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["submission_id"] == submission_id
    assert "status" in data

async def test_get_submission_history(
    client: AsyncClient,
    auth_headers,
    test_question,
    test_python_code
):
    # First make a submission
    await client.post(
        "/api/v1/code/submit",
        headers=auth_headers,
        json={
            "language": "python",
            "code": test_python_code,
            "question_id": str(test_question.id)
        }
    )
    
    # Then get history
    response = await client.get(
        "/api/v1/code/history",
        headers=auth_headers,
        params={"question_id": str(test_question.id)}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

async def test_get_question_submissions_as_admin(
    client: AsyncClient,
    admin_auth_headers,
    test_question
):
    response = await client.get(
        f"/api/v1/code/submissions/{test_question.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

async def test_get_question_submissions_as_user(
    client: AsyncClient,
    auth_headers,
    test_question
):
    response = await client.get(
        f"/api/v1/code/submissions/{test_question.id}",
        headers=auth_headers
    )
    assert response.status_code == 403
