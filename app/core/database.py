from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging

from app.core.config import settings
from app.models.user import User
from app.models.question import Question
from app.models.code_submission import CodeSubmission
from app.models.test_result import TestResult

logger = logging.getLogger(__name__)

async def init_db():
    """Initialize database connection"""
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # Test the connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Initialize beanie with the MongoDB client and document models
        logger.info(f"Initializing Beanie with database: {settings.DATABASE_NAME}")
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                User,
                Question,
                CodeSubmission,
                TestResult,
            ]
        )
        logger.info("Successfully initialized Beanie")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Failed to initialize database: {str(e)}\nTraceback: {error_details}")
        raise
