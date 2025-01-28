from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import List, Dict
import logging
import hashlib
from io import BytesIO
import os
import google.generativeai as genai
from document_processing import process_document_content, validate_file_type, SUPPORTED_MIMETYPES
from embedding import EmbeddingManager, BATCH_SIZE
from chunking import chunk_text
# Import the function
app = FastAPI()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize embedding manager
embedding_manager = EmbeddingManager()

# Storage
uploaded_documents: Dict[str, List[str]] = {}
processing_status = {}

class Query(BaseModel):
    question: str

def clean_and_format_context(matches: List[dict]) -> str:
    context_parts = []
    
    for i, match in enumerate(matches, 1):
        text = match['metadata']['text']
        page = match['metadata'].get('page', 'Unknown')
        context_part = f"[Excerpt {i} from page {page}]:\n{text.strip()}\n"
        context_parts.append(context_part)
    
    return "\n\n".join(context_parts)

async def process_chunks_batch(chunks: List[dict], file_name: str, task_id: str):
    try:
        texts = [chunk['text'] for chunk in chunks]
        embeddings = await embedding_manager.get_embeddings_batch(texts)
        
        if embeddings and len(embeddings) > 0:
            dimension = len(embeddings[0])
            await embedding_manager.initialize_index(dimension)
        
        vectors = []
        
        for chunk, embedding in zip(chunks, embeddings):
            if len(embedding) != dimension:
                raise embedding_manager.DimensionMismatchError(
                    f"Embedding dimension mismatch. Expected {dimension}, got {len(embedding)}"
                )
                
            vector_id = f"{file_name}-chunk-{chunk['index']}"
            
            if file_name not in uploaded_documents:
                uploaded_documents[file_name] = []
            uploaded_documents[file_name].append(vector_id)
            
            vectors.append({
                'id': vector_id,
                'values': embedding,
                'metadata': {
                    'text': chunk['text'],
                    'source': file_name,
                    'page': chunk.get('page', 1)
                }
            })
        
        if vectors:
            await asyncio.to_thread(lambda: embedding_manager.index.upsert(vectors=vectors))
        
        processing_status[task_id]['processed_chunks'] += len(chunks)
        processing_status[task_id]['progress'] = (
            processing_status[task_id]['processed_chunks'] / 
            processing_status[task_id]['total_chunks']
        ) * 100
        
    except embedding_manager.DimensionMismatchError as e:
        logger.error(str(e))
        processing_status[task_id]['status'] = 'failed'
        processing_status[task_id]['error'] = str(e)
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        processing_status[task_id]['status'] = 'failed'
        processing_status[task_id]['error'] = str(e)
        raise

async def process_document(file_bytes: bytes, filename: str, task_id: str):
    try:
        text_chunks = await process_document_content(file_bytes, filename)
        
        processing_status[task_id].update({
            'total_chunks': len(text_chunks),
            'processed_chunks': 0
        })
        
        tasks = []
        for i in range(0, len(text_chunks), BATCH_SIZE):
            batch = text_chunks[i:i + BATCH_SIZE]
            task = asyncio.create_task(process_chunks_batch(batch, filename, task_id))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        processing_status[task_id]['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        processing_status[task_id]['status'] = 'failed'
        processing_status[task_id]['error'] = str(e)
        raise

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# Hardcoded user credentials
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": "adminpassword",  # Use a hashed password in production
        "role": "admin"
    },
    "user": {
        "username": "user",
        "full_name": "Regular User",
        "email": "user@example.com",
        "hashed_password": "userpassword",  # Use a hashed password in production
        "role": "user"
    }
}

class User(BaseModel):
    username: str
    role: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/login")
async def login(formdata: OAuth2PasswordRequestForm = Depends()):
    print(formdata)
    user = fake_users_db.get(formdata.username)
    if not user or user['hashed_password'] != formdata.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    return {"access_token": user['username'], "token_type": "bearer", "role": user['role']}

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    try:
        logger.info(f"Received file: {file.filename}, Size: {file.size} bytes")  # Log file details
        
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_MIMETYPES.keys())}"
            )
        
        file_size = 0
        file_bytes = BytesIO()
        
        chunk_size = 1024 * 1024  # 1MB chunks
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(
                    status_code=400,
                    detail="File size exceeds 10MB limit"
                )
            file_bytes.write(chunk)
        
        file_bytes.seek(0)
        
        task_id = f"task_{hashlib.md5(file.filename.encode()).hexdigest()}"
        
        processing_status[task_id] = {
            'status': 'processing',
            'progress': 0,
            'processed_chunks': 0,
            'total_chunks': 0,
            'filename': file.filename
        }
        
        background_tasks.add_task(
            process_document,
            file_bytes.getvalue(),
            file.filename,
            task_id
        )
        
        return {
            "task_id": task_id,
            "message": "Document processing started",
            "filename": file.filename
        }
        
    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he.detail)}")  # Log HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")  # Log general errors
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in processing_status:
        return {"status": "not_found"}
    return processing_status[task_id]

@app.get("/documents")
async def list_documents():
    return {"documents": list(uploaded_documents.keys())}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    try:
        if filename not in uploaded_documents:
            raise HTTPException(status_code=404, detail="Document not found")
        
        vector_ids = uploaded_documents[filename]
        batch_size = 100
        for i in range(0, len(vector_ids), batch_size):
            batch = vector_ids[i:i + batch_size]
            embedding_manager.index.delete(ids=batch)
        
        del uploaded_documents[filename]
        return {"message": f"Document '{filename}' deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_document(query: Query):
    try:
        query_embedding = embedding_manager.get_cached_embedding(query.question)
        if not query_embedding:
            query_embedding = await asyncio.to_thread(
                lambda: genai.embed_content(
                    model=embedding_manager.embedding_model,
                    content=query.question,
                    task_type="retrieval_document"
                )['embedding']
            )
            embedding_manager.cache_embedding(query.question, query_embedding)
        
        dimension = len(query_embedding)
        await embedding_manager.initialize_index(dimension)
        
        search_results = await asyncio.to_thread(
            lambda: embedding_manager.index.query(
                vector=query_embedding,
                top_k=5,
                include_metadata=True
            )
        )
        
        reranked_matches = embedding_manager.rerank_results(search_results, query.question)
        context = clean_and_format_context(reranked_matches[:3])
        
        prompt = f"""Based on the following excerpts from a document, please answer the question accurately and completely. If the information needed to answer the question is not fully contained in the excerpts, please indicate this clearly.

Excerpts from document:
{context}

Question: {query.question}

Instructions:
1. Use only information from the provided excerpts
2. If the answer requires information not present in the excerpts, say so
3. If different excerpts contain contradicting information, point this out
4. Cite the excerpt numbers when providing information

Answer:"""
        
        response = await asyncio.to_thread(embedding_manager.model.generate_content, prompt)
        
        return {
            "answer": response.text,
            "sources": [f"Page {m['metadata'].get('page', 'Unknown')} of {m['metadata']['source']}" 
                       for m in reranked_matches[:3]]
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
