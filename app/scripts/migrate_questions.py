import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, PydanticObjectId

from app.core.config import settings
from app.models.question import Question
from app.models.user import User
from app.schemas.question import TestCase

async def migrate_questions():
    """Migrate existing questions to match the new schema"""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize beanie
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[Question, User]
    )
    
    # Get raw collection to bypass validation
    db = client[settings.DATABASE_NAME]
    questions_collection = db["questions"]
    
    # Get all questions as raw documents
    async for doc in questions_collection.find():
        updates = {}
        
        # Fix title_slug if title exists
        if "title" in doc:
            title = doc["title"]
            updates["title_slug"] = "-".join(title.lower().split())
        
        # Fix test cases
        if "test_cases" in doc:
            fixed_test_cases = []
            for test_case in doc["test_cases"]:
                # Ensure input and expected_output are strings
                test_case_dict = {
                    "input": str(test_case.get("input", "")),
                    "expected_output": str(test_case.get("expected_output", "")),
                    "timeout_ms": test_case.get("timeout_ms", 2000),
                    "memory_limit_mb": test_case.get("memory_limit_mb", 512),
                    "is_hidden": test_case.get("is_hidden", False)
                }
                fixed_test_cases.append(test_case_dict)
            updates["test_cases"] = fixed_test_cases
        else:
            # Add default test case if none exist
            updates["test_cases"] = [{
                "input": "",
                "expected_output": "",
                "timeout_ms": 2000,
                "memory_limit_mb": 512,
                "is_hidden": False
            }]
        
        # Fix created_by to be PydanticObjectId
        if "created_by" in doc:
            try:
                # If it's already an ObjectId, convert to PydanticObjectId
                if isinstance(doc["created_by"], (str, bytes)):
                    updates["created_by"] = PydanticObjectId(doc["created_by"])
            except:
                # If conversion fails, use a default admin user ID
                # You should replace this with a valid admin user ID
                updates["created_by"] = PydanticObjectId("000000000000000000000000")
        
        # Update the document if we have changes
        if updates:
            await questions_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": updates}
            )
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_questions())
