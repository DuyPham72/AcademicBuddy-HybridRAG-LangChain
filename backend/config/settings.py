import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Academic Buddy API"
    
    # Paths & URLs
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", 8000))
    
    # --- MODEL CONFIGURATION ---
    LLM_MODEL_NAME: str = "granite4:latest" 
    
    EMBEDDING_MODEL_NAME: str = "shatonix/granite-embedding-math-cs"
    EMBEDDING_DIM: int = 768 

settings = Settings()