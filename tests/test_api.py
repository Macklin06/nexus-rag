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

