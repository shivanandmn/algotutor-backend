from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List

from app.models.user import User
from app.schemas.code import (
    CodeSubmission,
    CodeSubmissionResponse,
    SubmissionHistory
)
from app.services.code_service import CodeExecutionService
from app.middleware.dev_auth import dev_auth_service

router = APIRouter()
code_service = CodeExecutionService()

@router.post("/submit", response_model=CodeSubmissionResponse)
async def submit_code(
    submission: CodeSubmission,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(dev_auth_service.get_current_user)
):
    """Submit code for execution"""
    try:
        # Queue the code execution
        submission_id = await code_service.queue_submission(
            user_id=str(current_user.id),
            submission=submission
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
    result = await code_service.get_submission_status(submission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if result.user_id != str(current_user.id) and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return result

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
    return submissions

@router.get("/submissions/{question_id}", response_model=List[SubmissionHistory])
async def get_question_submissions(
    question_id: str,
    current_user: User = Depends(dev_auth_service.get_current_user)
):
    """Get all submissions for a specific question (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    submissions = await code_service.get_question_submissions(question_id)
    return submissions
