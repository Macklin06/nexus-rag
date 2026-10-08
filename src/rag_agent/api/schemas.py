from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: int
    document_version_id: int
    chunk_index: int
    content: str
    rrf_score: float


class QueryResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]

class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceReference(BaseModel):
    chunk_id: int
    document_version_id: int
    chunk_index: int


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceReference]