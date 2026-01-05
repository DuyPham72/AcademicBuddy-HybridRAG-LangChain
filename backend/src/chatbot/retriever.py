from langchain_community.retrievers import BM25Retriever
from langchain_community.document_compressors import FlashrankRerank
from langchain_classic.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_core.documents import Document
from src.ingestion.vector_db import get_vector_store

def get_retriever_chain(file_filters=None):
    """
    Creates a Hybrid Retriever (Vector + Keyword) with Reranking.
    Accepts optional file_filters to restrict search.
    """
    vector_store = get_vector_store()
    
    # Configure Vector Search with Filters
    search_kwargs = {"k": 10}
    if file_filters:
        if len(file_filters) == 1:
             search_kwargs["filter"] = {"filename": file_filters[0]}
        else:
             search_kwargs["filter"] = {"filename": {"$in": file_filters}}

    base_vector_retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

    try:
        # Configure BM25 (Keyword) Search with Filters
        data = vector_store.get() 
        if not data or not data['documents']:
            return None
            
        doc_objects = []
        for t, m in zip(data['documents'], data['metadatas']):
            if file_filters and m.get("filename") not in file_filters:
                continue
            doc_objects.append(Document(page_content=t, metadata=m))
        
        if not doc_objects:
            return None

        bm25_retriever = BM25Retriever.from_documents(doc_objects)
        bm25_retriever.k = 10
        
        # Combine those 2 search with weights (0.3/0.7)
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, base_vector_retriever],
            weights=[0.3, 0.7]
        )
        
        # Rerank the retrieval result
        compressor = FlashrankRerank(model='ms-marco-MiniLM-L-12-v2', top_n=5)
        
        final_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, 
            base_retriever=ensemble_retriever
        )
        
        return final_retriever

    except Exception as e:
        print(f"Hybrid Retriever initialization failed: {e}")
        return base_vector_retriever
    
def get_smart_display_name(doc):
    """
    Helper function to extract the best possible label for a document chunk.
    Prioritizes Markdown headers, falls back to text preview.
    """
    for key in ["Subsection", "Section", "Title"]:
        if header := doc.metadata.get(key):
            return header

    clean_text = doc.page_content.replace("#", "").replace("*", "").strip()
    return " ".join(clean_text.split()[:5]) + "..."

def filter_by_score(docs, threshold=0.7):
    """
    Filters documents based on the Reranker's relevance score.
    """
    filtered = []
    for d in docs:
        score = d.metadata.get("relevance_score", 0.0)
        
        if score >= threshold:
            filtered.append(d)
        else:
            print(f"Dropped chunk '{get_smart_display_name(d)}' (Score: {score:.4f})")
            
    return filtered