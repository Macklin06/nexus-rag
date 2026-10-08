from fastapi.testclient import TestClient
from rag_agent.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == "API is running"

def test_create_and_get_document():
    response = client.post(
        "/documents",
        headers={"api-key":"dev-test-key"},
        json={
            "title": "Mine Safety",

            "content": "Safety guidelines",

            "source": "DGMS",
        },)

    assert response.status_code == 202

    data = response.json()
    document_id = data["id"]


    response = client.get(

        f"/documents/{document_id}",

        headers={"api-key": "dev-test-key"},

    )

    assert response.status_code == 200

    assert response.json()["title"] == "Mine Safety"

def test_invalid_api_key():
    response = client.get(
        "/documents/1",
        headers={"api-key":"wrong-api-key"},
    )

    assert response.status_code == 401

def test_missing_document():
    response = client.get(
        "/documents/999999",
        headers={"api-key": "dev-test-key"},
    )

    assert response.status_code == 404

def test_rate_limit():
    from rag_agent.api import main

    original_limit = main.rate_limiter.limit
    original_api_key = main.API_KEY

    test_api_key = "rate-limit-test-key"
    main.API_KEY = test_api_key
    main.rate_limiter.limit = 2

    try:
        first = client.get(
            "/documents/999999",
            headers={"api-key": test_api_key},
        )
        second = client.get(
            "/documents/999999",
            headers={"api-key": test_api_key},
        )
        third = client.get(
            "/documents/999999",
            headers={"api-key": test_api_key},
        )

        assert first.status_code == 404
        assert second.status_code == 404
        assert third.status_code == 429
    finally:
        main.API_KEY = original_api_key
        main.rate_limiter.limit = original_limit

def test_generation_failure_returns_503(monkeypatch):
    from rag_agent.api import main

    def failing_generate(prompt):
        raise RuntimeError("Ollama unavailable")

    monkeypatch.setattr(main, "generate", failing_generate)

    response = client.post(
        "/ask",
        headers={"api-key": "dev-test-key"},
        json={
            "query": "What does Nexus-RAG store?",
            "top_k": 1,
        },
    )

    assert response.status_code == 503
    assert response.json()["error"] == "Generation service unavailable"

def test_query_cache_redis_failure_is_non_fatal():
    from rag_agent.cache.query_cache import QueryCache
    import redis

    class FailingRedis:
        def get(self, key):
            raise redis.RedisError("Redis unavailable")

        def setex(self, key, ttl, value):
            raise redis.RedisError("Redis unavailable")

    cache = QueryCache(FailingRedis())

    assert cache.get("test query", 5) is None

    cache.set(
        "test query",
        5,
        '{"answer":"test"}',
    )

def test_retrieval_database_failure_returns_503():
    from rag_agent.api import main
    from sqlalchemy.exc import SQLAlchemyError

    class FailingSession:
        def execute(self, statement):
            raise SQLAlchemyError("Postgres unavailable")

    def fake_get_db():
        yield FailingSession()

    main.app.dependency_overrides[main.get_db] = fake_get_db

    try:
        response = client.post(
            "/ask",
            headers={"api-key": "dev-test-key"},
            json={
                "query": "Explain Nexus-RAG storage architecture test 938271",
                "top_k": 1,
            },
        )

        assert response.status_code == 503
        assert response.json()["error"] == "Retrieval service unavailable"
    finally:
        main.app.dependency_overrides.clear()

