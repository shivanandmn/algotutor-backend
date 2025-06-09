from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    # App settings
    APP_NAME: str = os.getenv("APP_NAME", "MyCodeJudge")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # MongoDB settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "mycodejudge")
    
    # Auth settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React frontend
        "http://localhost:8000"   # FastAPI backend
    ]

settings = Settings()
