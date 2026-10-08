import os
import time
import asyncio
import redis
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from rag_agent.db.database import get_db
from rag_agent.db.models import Document, DocumentVersion
from rag_agent.ingestion.jobs import IngestionJob
from rag_agent.ingestion.queue import IngestionQueue
from rag_agent.ingestion.hashing import content_hash
from rag_agent.api.schemas import (
    AskRequest,
    AskResponse,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
    SourceReference,
)
from rag_agent.ingestion.embeddings import embed_text
from rag_agent.retrieval.vector import (
    build_full_text_search_query,
    build_vector_search_query,
    reciprocal_rank_fusion,
)
from rag_agent.generation.llm import generate
from rag_agent.generation.prompts import build_grounded_prompt
from rag_agent.cache.query_cache import QueryCache
from rag_agent.api.rate_limit import RateLimiter


load_dotenv()

API_KEY = os.getenv("API_KEY")

redis_client = redis.Redis.from_url(
    os.environ["REDIS_URL"],
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=None,
)

query_cache = QueryCache(
    redis_client,
    ttl=int(os.getenv("QUERY_CACHE_TTL", "300")),
)

rate_limiter = RateLimiter(
    redis_client,
    limit=int(os.getenv("RATE_LIMIT", "60")),
    window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
)

ingestion_queue = IngestionQueue(redis_client)


app = FastAPI()

class DocumentCreate(BaseModel):
    title : str
    content : str
    source : str

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    source: str
    content_hash: str
    current_version: int

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    if not rate_limiter.allow(api_key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )

    return api_key


@app.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=202,
    dependencies=[Depends(verify_api_key)],
)
def create(
    document: DocumentCreate,
    db: Session = Depends(get_db),
):
    content_digest = content_hash(document.content)

    doc = Document(
        title=document.title,
        content=document.content,
        source=document.source,
        content_hash=content_digest,
        current_version=1,
    )

    db.add(doc)
    db.flush()

    version = DocumentVersion(
        document_id=doc.id,
        version=1,
        content=document.content,
        content_hash=content_digest,
    )

    db.add(version)
    db.commit()
    db.refresh(doc)
    db.refresh(version)

    ingestion_queue.enqueue(
        IngestionJob(document_version_id=version.id)
    )

    return doc

@app.get("/documents/{document_id}", response_model=DocumentResponse, dependencies=[Depends(verify_api_key)])
def get_document(document_id: int, db: Session = Depends(get_db)):
    cache_key = f"document:{document_id}"
    cached_value = redis_client.get(cache_key)
    print("CACHE LOOKUP:", cache_key, cached_value)

    if cached_value is None:
        document = db.get(Document,document_id)
        print("CACHE MISS → QUERYING POSTGRES")
        
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        document_data = {
            "id": document.id,
            "title": document.title,
            "content": document.content,
            "source": document.source
        }

        redis_client.set(cache_key,json.dumps(document_data),ex=60)
        
        return document
    else:
        print("CACHE HIT → RETURNING FROM REDIS")
        return json.loads(cached_value)

@app.put("/documents/{document_id}", response_model=DocumentResponse, dependencies=[Depends(verify_api_key)])
def update_document(
    document_id: int,
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    existing_document = db.get(Document, document_id)

    if existing_document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    existing_document.title = document.title
    existing_document.content = document.content
    existing_document.source = document.source

    db.commit()
    db.refresh(existing_document)

    redis_client.delete(f"document:{document_id}")

    return existing_document

@app.delete("/documents/{document_id}", dependencies=[Depends(verify_api_key)])

def delete_document(document_id: int, db: Session = Depends(get_db)):

    document = db.get(Document,document_id)

    if document is None:

        raise HTTPException(

            status_code=404,

            detail="Document not found"

        )

    db.delete(document)
    db.commit()

    redis_client.delete(f"document:{document_id}")

    return {"message": "Document deleted"}


@app.get("/health")
def health():
    return "API is running"


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )

@app.get("/sync-sleep")
def sync_sleep():
    time.sleep(2)
    return {"message": "sync done"}

@app.get("/async-sleep")
async def async_sleep():
    await asyncio.sleep(2)
    return {"message":"async done"}

@app.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=202,
    dependencies=[Depends(verify_api_key)],
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if file.filename is None:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    if not file.filename.endswith((".txt", ".md")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .md files are supported",
        )

    raw_content = await file.read()

    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded",
        ) from exc

    if not content.strip():
        raise HTTPException(
            status_code=400,
            detail="File cannot be empty",
        )

    content_digest = content_hash(content)

    doc = Document(
        title=file.filename,
        content=content,
        source=f"upload:{file.filename}",
        content_hash=content_digest,
        current_version=1,
    )

    db.add(doc)
    db.flush()

    version = DocumentVersion(
        document_id=doc.id,
        version=1,
        content=content,
        content_hash=content_digest,
    )

    db.add(version)
    db.commit()

    db.refresh(doc)
    db.refresh(version)

    ingestion_queue.enqueue(
        IngestionJob(document_version_id=version.id)
    )

    return doc

@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
def query_documents(request: QueryRequest, db: Session = Depends(get_db)):
    query_embedding = embed_text(request.query)

    vector_statement = build_vector_search_query(
        query_embedding=query_embedding,
        top_k=request.top_k,
    )
    vector_rows = db.execute(vector_statement).all()

    vector_chunks = {chunk.id: chunk for chunk, _ in vector_rows}
    vector_ranked_ids = [chunk.id for chunk, _ in vector_rows]

    full_text_statement = build_full_text_search_query(
        query=request.query,
        top_k=request.top_k,
    )
    full_text_rows = db.execute(full_text_statement).all()

    full_text_chunks = {chunk.id: chunk for chunk, _ in full_text_rows}
    full_text_ranked_ids = [chunk.id for chunk, _ in full_text_rows]

    fused_results = reciprocal_rank_fusion(
        [vector_ranked_ids, full_text_ranked_ids]
    )

    all_chunks = {**vector_chunks, **full_text_chunks}

    results = [
        RetrievedChunk(
            chunk_id=chunk_id,
            document_version_id=all_chunks[chunk_id].document_version_id,
            chunk_index=all_chunks[chunk_id].chunk_index,
            content=all_chunks[chunk_id].content,
            similarity=rrf_score,
        )
        for chunk_id, rrf_score in fused_results[:request.top_k]
    ]

    return QueryResponse(
        query=request.query,
        results=results,
    )

@app.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(verify_api_key)],
)
def ask_documents(request: AskRequest, db: Session = Depends(get_db)):
    cached_response = query_cache.get(
        request.query,
        request.top_k,
    )

    if cached_response is not None:
        return AskResponse.model_validate_json(cached_response)

    query_embedding = embed_text(request.query)
    
    try:

        vector_statement = build_vector_search_query(
            query_embedding=query_embedding,
            top_k=request.top_k,
        )
        vector_rows = db.execute(vector_statement).all()

        vector_chunks = {chunk.id: chunk for chunk, _ in vector_rows}
        vector_ranked_ids = [chunk.id for chunk, _ in vector_rows]

        full_text_statement = build_full_text_search_query(
            query=request.query,
            top_k=request.top_k,
        )
        full_text_rows = db.execute(full_text_statement).all()

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Retrieval service unavailable",
        ) from exc

    full_text_chunks = {chunk.id: chunk for chunk, _ in full_text_rows}
    full_text_ranked_ids = [chunk.id for chunk, _ in full_text_rows]

    fused_results = reciprocal_rank_fusion(
        [vector_ranked_ids, full_text_ranked_ids]
    )

    all_chunks = {**vector_chunks, **full_text_chunks}

    selected_chunks = [
        all_chunks[chunk_id]
        for chunk_id, _ in fused_results[:request.top_k]
    ]

    contexts = [
        {
            "chunk_id": chunk.id,
            "document_version_id": chunk.document_version_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk in selected_chunks
    ]

    prompt = build_grounded_prompt(
        question=request.query,
        contexts=contexts,
    )

    try:
        answer = generate(prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Generation service unavailable",
        ) from exc

    sources = [
        SourceReference(
            chunk_id=chunk.id,
            document_version_id=chunk.document_version_id,
            chunk_index=chunk.chunk_index,
        )
        for chunk in selected_chunks
    ]

    response = AskResponse(
        query=request.query,
        answer=answer,
        sources=sources,
    )

    query_cache.set(
        request.query,
        request.top_k,
        response.model_dump_json(),
    )

    return response