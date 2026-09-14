import os
import time
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from rag_agent.db.database import get_db
from rag_agent.db.models import Document


load_dotenv()

API_KEY = os.getenv("API_KEY")

app = FastAPI()

class DocumentCreate(BaseModel):
    title : str
    content : str
    source : str

class DocumentResponse(BaseModel):
    id : int
    title : str
    content : str
    source : str

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key


@app.post("/documents", response_model=DocumentResponse, dependencies=[Depends(verify_api_key)])
def create(document: DocumentCreate, db: Session = Depends(get_db)):
    doc = Document(
        title=document.title,
        content=document.content,
        source=document.source,
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return doc

@app.get("/documents/{document_id}", response_model=DocumentResponse, dependencies=[Depends(verify_api_key)])
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document,document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

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