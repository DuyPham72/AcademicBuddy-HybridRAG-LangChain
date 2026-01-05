import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import chat, documents
from config.settings import settings

@asynccontextmanager
async def lifespan():
    """
    Lifespan context manager that ensures the LLM model is available 
    before the application starts accepting requests.
    """
    ollama_url = settings.OLLAMA_URL
    target_model = settings.LLM_MODEL_NAME

    print(f"Checking model availability: {target_model}...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Check if model exists
            resp = await client.get(f"{ollama_url}/api/tags")
            existing_models = [m['name'] for m in resp.json().get('models', [])]
            
            # Check for exact match or has :latest tag
            if target_model not in existing_models and f"{target_model}:latest" not in existing_models:
                print(f"Model '{target_model}' not found. Pulling from Ollama library...")
                print("(This may take a while depending on file size...)")
                
                # Trigger Pull
                pull_resp = await client.post(
                    f"{ollama_url}/api/pull", 
                    json={"name": target_model, "stream": False},
                    timeout=None 
                )
                
                if pull_resp.status_code == 200:
                    print(f"Successfully pulled '{target_model}'!")
                else:
                    print(f"Failed to pull model: {pull_resp.text}")
            else:
                print(f"Model '{target_model}' is already available.")
                
        except Exception as e:
            print(f"Could not connect to Ollama at {ollama_url}.")
            print(f"Error details: {e}")

    yield 
    
    print("Shutting down Academic Buddy...")

# --- Initialize App ---
app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

# --- Add CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

@app.get("/")
async def root():
    return {"status": "running", "message": "Academic Buddy Backend is Live"}