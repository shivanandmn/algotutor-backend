from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from datetime import datetime

from app.models.user import User
from app.models.question import Question
from app.schemas.code import (
    CodeSubmissionRequest,
    CodeSubmissionResponse,
    SubmissionHistory
)
from app.models.code_submission import CodeSubmission
from app.services.code_service import CodeExecutionService
from app.middleware.dev_auth import dev_auth_service
from beanie import PydanticObjectId

router = APIRouter()
code_service = CodeExecutionService()

from app.schemas.code import CodeSubmissionRequest  # Add this import at the top

@router.post("/submit", response_model=CodeSubmissionResponse)
async def submit_code(
    submission: CodeSubmissionRequest,  # Use the request schema
    background_tasks: BackgroundTasks,
    current_user: User = Depends(dev_auth_service.get_current_user)
):
    """Submit code for execution"""
    try:
        # Validate question exists
        question = await Question.get(PydanticObjectId(submission.question_id))
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Queue the code execution
        submission_id = await code_service.queue_submission(
            user_id=str(current_user.id),
            question_id=submission.question_id,
            language=submission.language,
            code=submission.code
        )
        
        # Execute code in background
        background_tasks.add_task(
            code_service.execute_submission,
            submission_id=submission_id
        )
        
        return {
            "submission_id": submission_id,
            "status": "queued",
            "message": "Code submission queued for execution",
            "error": False,
            "success": True,
            "total_passed": 0,
            "total_tests": 0,
            "execution_time": 0,
            "memory_used": 0,
            "submitted_at": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{submission_id}", response_model=CodeSubmissionResponse)
async def get_submission_status(
    submission_id: str,
    current_user: User = Depends(dev_auth_service.get_current_user)
):
    """Get the status of a code submission"""
    result = await CodeSubmission.get(PydanticObjectId(submission_id))
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Handle both DBRef and ObjectId cases for user field
    user_id = str(result.user.id if hasattr(result.user, 'id') else result.user)
    if user_id != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Handle both DBRef and ObjectId cases for question field
    question_id = str(result.question.id if hasattr(result.question, 'id') else result.question)
    
    return {
        "submission_id": str(result.id),
        "user": str(user_id),
        "question": question_id,
        "language": result.language,
        "code": result.code,
        "status": result.status,
        "message": f"Submission status: {result.status}",
        "results": result.results or [],
        "total_passed": result.total_passed,
        "total_tests": result.total_tests,
        "execution_time": result.execution_time,
        "memory_used": result.memory_used,
        "error": result.status == "error",
        "success": result.status == "completed",
        "submitted_at": result.submitted_at
    }

@router.get("/history", response_model=List[SubmissionHistory])
async def get_submission_history(
    question_id: str = None,
    current_user: User = Depends(dev_auth_service.get_current_user)
):
    """Get submission history for the current user"""
    submissions = await code_service.get_user_submissions(
        user_id=str(current_user.id),
        question_id=question_id
    )
    
    # Format submissions to match SubmissionHistory schema
    return [{
        "_id": str(sub.id),
        "user": str(sub.user.id if hasattr(sub.user, 'id') else sub.user),
        "question_id": str(sub.question.id if hasattr(sub.question, 'id') else sub.question),
        "language": sub.language,
        "code": sub.code,
        "status": sub.status,
        "results": sub.results or [],
        "submitted_at": sub.submitted_at
    } for sub in submissions]

@router.get("/submissions/{question_id}", response_model=List[SubmissionHistory])
async def get_question_submissions(
    question_id: str,
    current_user: User = Depends(dev_auth_service.get_current_user)
):
    """Get all submissions for a specific question (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    submissions = await code_service.get_question_submissions(question_id)
    
    # Format submissions to match SubmissionHistory schema
    return [{
        "_id": str(sub.id),
        "user": str(sub.user.id if hasattr(sub.user, 'id') else sub.user),
        "question_id": str(sub.question.id if hasattr(sub.question, 'id') else sub.question),
        "language": sub.language,
        "code": sub.code,
        "status": sub.status,
        "results": sub.results or [],
        "submitted_at": sub.submitted_at
    } for sub in submissions]
