import json
import asyncio
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from config.schemas import ChatRequest
from src.chatbot.rag_chains import get_chat_chain, get_query_transform_chain
from src.chatbot.retriever import get_retriever_chain, get_smart_display_name, filter_by_score

router = APIRouter()

@router.post("/")
async def chat(request: ChatRequest):
    return StreamingResponse(
        generate_chat_response(request.message, request.history, request.selected_files),
        media_type="application/x-ndjson"
    )

async def generate_chat_response(message: str, history: list, selected_files: list = None):
    try:
        # 1. PREPARE HISTORY
        langchain_history = []
        for msg in history:
            if msg.role == "user":
                langchain_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_history.append(AIMessage(content=msg.content))

        # 2. QUERY REWRITING
        search_query = message
        is_rewritten = False
        
        if langchain_history:
            rewrite_chain = get_query_transform_chain()
            try:
                search_query = await asyncio.to_thread(
                    rewrite_chain.invoke, 
                    {"chat_history": langchain_history, "input": message}
                )
                is_rewritten = True
                print(f"Rewritten Query: '{search_query}'")
            except Exception as e:
                print(f"Query rewriting failed: {e}")

        # 3. RETRIEVAL (Single Query + File Filter)
        retriever = get_retriever_chain(file_filters=selected_files)
        if not retriever:
            yield json.dumps({"type": "error", "data": "Knowledge base empty."}) + "\n"
            return

        # Attempt 1: Search with (potentially rewritten) query
        docs = await asyncio.to_thread(retriever.invoke, search_query)

        print(f"\nRaw Results for '{search_query}':")
        for i, d in enumerate(docs):
            score = d.metadata.get("relevance_score", 0.0)
            print(f"   [{i+1}] Score: {score:.4f} | {get_smart_display_name(d)}")
        print("-" * 40)
        
        # Filter by score
        docs = filter_by_score(docs, threshold=0.7)

        # If filtering removed everything, try original query
        if not docs and is_rewritten:
            print(f"No relevant docs found for rewritten query. Retrying with original: '{message}'")
            docs = await asyncio.to_thread(retriever.invoke, message)
            docs = filter_by_score(docs, threshold=0.7)

        if not docs:
            print("No relevant documents found above threshold.")
            yield json.dumps({"type": "content", "data": "Information Not Included."}) + "\n"
            return

        # 4. SEND SOURCES
        sources_data = []
        for d in docs:
            filename = os.path.basename(d.metadata.get("source", "Unknown"))
            content_preview = d.page_content[:500].replace("\n", " ")
            display_name = get_smart_display_name(d)
            
            # Page Number Logic
            page = d.metadata.get("page_number", "N/A")
            display_label = f"{display_name} (p.{page})"
            
            sources_data.append({
                "source": filename,
                "display": display_label,
                "content": content_preview
            })
        
        yield json.dumps({"type": "sources", "data": sources_data}) + "\n"

        # 5. GENERATION
        context_text = "\n\n".join([d.page_content for d in docs])
        rag_chain = get_chat_chain()

        async for chunk in rag_chain.astream({
            "context": context_text,
            "chat_history": langchain_history, 
            "input": message
        }):
            if chunk:
                yield json.dumps({"type": "content", "data": chunk}) + "\n"

    except Exception as e:
        print(f"Server Error: {e}")
        yield json.dumps({"type": "error", "data": f"Server Error: {str(e)}"}) + "\n"