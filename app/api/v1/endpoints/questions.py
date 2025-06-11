from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from beanie import PydanticObjectId

from app.models.user import User
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/", response_model=Question)
async def create_question(
    question: QuestionCreate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Create a new question"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Create slug from title
    title_slug = "_".join(question.title.lower().split())
    
    # Check if slug exists
    existing = await Question.find_one({"title_slug": title_slug})
    if existing:
        raise HTTPException(status_code=400, detail="Question with this title already exists")
    
    db_question = Question(
        **question.dict(),
        title_slug=title_slug,
        created_by=current_user.id,  # This is already a PydanticObjectId
        likes=0,
        dislikes=0
    )
    await db_question.insert()
    return db_question

@router.get("/", response_model=List[Question])
async def list_questions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    difficulty: Optional[str] = Query(None, pattern="^(easy|medium|hard)$"),
    topics: Optional[List[str]] = Query(None),
    companies: Optional[List[str]] = Query(None)
):
    """List questions with filters"""
    query = {}
    
    if difficulty:
        query["level"] = difficulty
    if topics:
        query["topics"] = {"$all": topics}
    if companies:
        query["companies"] = {"$all": companies}
        
    questions = await Question.find(query).skip(skip).limit(limit).to_list()
    return questions

@router.get("/{slug}", response_model=Question)
async def get_question(slug: str = Path(..., title="Question slug")):
    """Get a question by slug"""
    question = await Question.find_one({"title_slug": slug})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/{id}/like")
async def like_question(
    id: PydanticObjectId,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Like a question"""
    question = await Question.get(id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Update likes count
    question.likes += 1
    await question.save()
    
    return {"message": "Question liked successfully"}

@router.post("/{id}/dislike")
async def dislike_question(
    id: PydanticObjectId,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Dislike a question"""
    question = await Question.get(id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Update dislikes count
    question.dislikes += 1
    await question.save()
    
    return {"message": "Question disliked successfully"}

@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    """Get a specific question by ID"""
    try:
        question = await Question.get(PydanticObjectId(question_id))
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question
    except:
        raise HTTPException(status_code=404, detail="Question not found")

@router.patch("/{question_id}", response_model=Question)
async def update_question(
    question_id: str,
    question_update: QuestionUpdate,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Update a question"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    question = await Question.get(PydanticObjectId(question_id))
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await question.update({"$set": question_update.dict(exclude_unset=True)})
    return question

@router.delete("/{question_id}")
async def delete_question(
    question_id: str,
    current_user: User = Depends(auth_service.get_current_user)
):
    """Delete a question"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    question = await Question.get(PydanticObjectId(question_id))
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await question.delete()
    return {"message": "Question deleted successfully"}
