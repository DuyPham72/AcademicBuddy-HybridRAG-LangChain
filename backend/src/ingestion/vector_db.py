from functools import lru_cache
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings

@lru_cache(maxsize=1)
def get_embedding_function():
    """
    Returns the embedding function. 
    Cached to prevent reloading the model on every request.
    """
    embedding_fn = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True}
    )
    return embedding_fn

def get_vector_store():
    """
    Returns the ChromaDB instance using the custom embedding function
    """
    return Chroma(
        collection_name="academic_docs",
        embedding_function=get_embedding_function(),
        client_settings=None,
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT
    )