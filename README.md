# Nexus-RAG

Nexus-RAG is a retrieval-augmented generation (RAG) application with hybrid retrieval, asynchronous ingestion, and API-based access.

## Architecture
- API: FastAPI
- Database: PostgreSQL with pgvector
- Retrieval: Vector search, PostgreSQL full-text search, and reciprocal rank fusion (RRF)
- Ingestion: Redis-backed queue and separate Python worker
- Embeddings: Sentence Transformers, 384 dimensions
- Generation: Ollama
- Deployment: Docker Compose

## Features
- API-key authentication and request rate limiting
- Redis-backed caching
- Asynchronous document ingestion
- Versioned document storage
- Hybrid vector and full-text retrieval
- Golden-set retrieval evaluation

## Requirements
- Docker and Docker Compose
- Python 3.13 or later for local development
- Ollama running on the host with the configured model available

## Run
Create a local .env file with the required configuration. Never commit secrets.

Review docker-compose.yml and ensure the database credentials and Ollama endpoint match your environment.

Start the services:
```bash
docker compose up --build -d
```

Apply database migrations from an environment where DATABASE_URL points to the intended database:
```bash
alembic upgrade head
```

Check API health at /health on port 8000.

## API
Authenticated endpoints use the api-key request header.
- GET /health — health check
- POST /documents — submit a document for ingestion
- POST /documents/upload — upload a text or Markdown file
- POST /query — retrieve relevant chunks
- POST /ask — generate an answer using retrieved context

## Evaluation
See evaluation/README.md for benchmark details and reproduction instructions.

Current benchmark: 14 questions; Evidence Recall@5 = 0.714; MRR@5 = 0.389.
These metrics measure evidence retrieval, not generated-answer correctness or citation faithfulness.

## Tests
```bash
pip install -e '.[dev]'
pytest
```

## Limitations
The benchmark is small and has known retrieval misses. Document versioning exists in the schema, but version-aware retrieval and document-update workflows need further work. Review development credentials and configuration before deployment.

## License
No license has been specified. All rights reserved unless a license is added.
