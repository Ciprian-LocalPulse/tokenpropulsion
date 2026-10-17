import pytest
from fastapi.testclient import TestClient

from tokenpropulsion.api.app import create_app

TOKEN = "test-token-is-at-least-thirty-two-characters"


def test_configuration(monkeypatch):
    monkeypatch.delenv("TOKENPROPULSION_API_TOKEN", raising=False)
    for token in [None, "short", "ă" * 40]:
        with pytest.raises(ValueError):
            create_app(api_token=token)
    monkeypatch.setenv("TOKENPROPULSION_API_TOKEN", TOKEN)
    assert create_app()


def test_auth_and_endpoints():
    client = TestClient(create_app(api_token=TOKEN))
    assert client.get("/health").status_code == 401
    client.headers["Authorization"] = "Bearer " + TOKEN
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/version").json()["version"] == "1.0.0rc1"
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    for endpoint in ["/compress", "/analyze"]:
        result = client.post(endpoint, json={"text": "Hello.   "})
        assert result.status_code == 200
        assert result.json()["optimized_text"] == "Hello."
    for payload in [
        {"text": 1},
        {"text": "x", "level": "bad"},
        {"text": "x", "extra": "PRIVATE"},
        {"text": "\0"},
    ]:
        response = client.post("/compress", json=payload)
        assert response.status_code == 422
        assert "PRIVATE" not in response.text
    assert client.post("/compress", content=b"not json").status_code == 422
    assert client.post("/compress", content=b"x" * 1000001).status_code == 413
    assert (
        client.post("/compress", content=b"x", headers={"Content-Encoding": "gzip"}).status_code
        == 415
    )


def test_streamed_limit():
    client = TestClient(create_app(api_token=TOKEN))
    client.headers["Authorization"] = "Bearer " + TOKEN
    chunks = (b"x" * 400000 for _ in range(3))
    assert client.post("/compress", content=chunks).status_code == 413
