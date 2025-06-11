from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from beanie import PydanticObjectId

from app.models.user import User
from app.models.question import Question
from app.models.solution import Solution
from app.schemas.solution import SolutionCreate, Solution as SolutionSchema
from app.services.auth_service import AuthService
from app.services.code_service import CodeExecutionService

router = APIRouter()
auth_service = AuthService()
code_service = CodeExecutionService()

@router.post("/{slug}", response_model=SolutionSchema)
async def submit_code(
    slug: str,
    solution: SolutionCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Submit code for a question"""
    # Get question
    question = await Question.find_one({"title-slug": slug})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Create solution
    db_solution = Solution(
        question=question.id,
        user=current_user.id,
        lang=solution.lang,
        lang_slug=solution.lang_slug,
        code=solution.code
    )
    await db_solution.insert()
    
    # Execute code
    result = await code_service.execute_code(
        code=solution.code,
        lang=solution.lang_slug,
        input_data=question.test_cases.input
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return db_solution

@router.get("/{id}", response_model=SolutionSchema)
async def get_submission(
    id: PydanticObjectId,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get a submission by ID"""
    solution = await Solution.get(id)
    if not solution:
        raise HTTPException(status_code=404, detail="Submission notfound")
    
    # Check if user owns submission
    if str(solution.user.id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return solution

@router.get("/user/{user_id}", response_model=List[SolutionSchema])
async def get_user_submissions(
    user_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get all submissions for a user"""
    # Check if user is requesting their own submissions
    if user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    solutions = await Solution.find(
        {"user": PydanticObjectId(user_id)}
    ).to_list()
    
    return solutions
