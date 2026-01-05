from langchain_ollama import ChatOllama
from config.settings import settings

def get_llm(streaming):
    """
    Connects to the Fine-Tuned Reasoning Model in Ollama
    """
    llm = ChatOllama(
        base_url=settings.OLLAMA_URL,
        model=settings.LLM_MODEL_NAME,
        temperature=0.2,
        keep_alive="1h",
        streaming=streaming
    )
    return llm