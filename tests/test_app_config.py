from fastapi.testclient import TestClient

from app.main import app


def test_local_root_path_is_empty() -> None:
    assert app.root_path == ""


def test_docs_are_available() -> None:
    client = TestClient(app)

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_docs_use_local_openapi_url() -> None:
    client = TestClient(app)

    response = client.get("/docs")

    assert response.status_code == 200
    assert "/openapi.json" in response.text
    assert "/default/openapi.json" not in response.text


def test_docs_use_root_path_openapi_url(monkeypatch) -> None:
    monkeypatch.setattr(app, "root_path", "/default")
    client = TestClient(app)

    response = client.get("/docs")

    assert response.status_code == 200
    assert "/default/openapi.json" in response.text


def test_health_route_still_uses_internal_path() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_json_is_available_locally() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Purchase Requests API"
