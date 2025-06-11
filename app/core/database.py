from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.user import User
from app.models.question import Question
from app.models.code_submission import CodeSubmission
from app.models.test_result import TestResult

async def init_db():
    """Initialize database connection"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize beanie with the MongoDB client and document models
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[
            User,
            Question,
            CodeSubmission,
            TestResult,
        ]
    )
