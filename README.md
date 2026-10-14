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

## Project Structure

```text
nexus-rag/
├── src/
│   └── rag_agent/
│       └── api/                 # FastAPI application
├── evaluation/
│   ├── evaluate_retrieval.py    # Retrieval benchmark evaluator
│   └── README.md                # Evaluation methodology and results
├── migrations/                  # Alembic database migrations
├── tests/                       # Automated test suite
├── worker.py                    # Asynchronous ingestion worker
├── async_experiment.py          # Async experiment script
├── Dockerfile                   # Application container
├── docker-compose.yml           # Local multi-service deployment
├── alembic.ini                  # Migration configuration
├── pyproject.toml               # Dependencies and project metadata
├── .env.example                 # Environment configuration template
├── .dockerignore
├── .gitignore
└── README.md
```

### Main Components

- `src/rag_agent/`: Core application and RAG API code.
- `worker.py`: Processes queued document-ingestion jobs.
- `migrations/`: Database schema migrations managed by Alembic.
- `evaluation/`: Golden-set retrieval evaluation and documented metrics.
- `tests/`: Automated tests for application behavior.
- `docker-compose.yml`: Defines the local application services.
- `pyproject.toml`: Project metadata and Python dependencies.
## Requirements
- Docker and Docker Compose
- Python 3.13 or later for local development
- Ollama running on the host with the configured model available

## Run
Copy `.env.example` to `.env` and replace the API key placeholder. Never commit `.env` or real credentials.

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
