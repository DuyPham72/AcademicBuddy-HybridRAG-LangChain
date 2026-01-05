import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from src.ingestion.loader import load_file_with_docling
from src.ingestion.splitter import split_documents
from src.ingestion.vector_db import get_vector_store

router = APIRouter()

@router.get("/")
def list_files():
    store = get_vector_store()
    data = store.get()
    unique_files = set()
    if data and 'metadatas' in data:
        for m in data['metadatas']:
            if m.get('filename'): unique_files.add(m['filename'])
    return {"files": list(unique_files)}

@router.delete("/{filename}")
def delete_file(filename: str):
    store = get_vector_store()
    try:
        store._collection.delete(where={"filename": filename})
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        print(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        try:
            raw_docs = load_file_with_docling(temp_path)
            for doc in raw_docs: doc.metadata["filename"] = file.filename
            chunks = split_documents(raw_docs)
            if chunks:
                store = get_vector_store()
                store.add_documents(chunks)
                results.append(file.filename)
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)
    return {"uploaded": results}