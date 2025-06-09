from fastapi import APIRouter
from app.api.v1.endpoints import auth, code, questions

# Create the main v1 router
router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(code.router, prefix="/code", tags=["code"])
router.include_router(questions.router, prefix="/questions", tags=["questions"])
