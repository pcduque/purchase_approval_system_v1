from uuid import UUID
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.main import app
from app.models.request import PurchaseRequest


class FakeRequestRepository:
    def __init__(self) -> None:
        self.saved_requests: list[PurchaseRequest] = []

    def save(self, purchase_request: PurchaseRequest) -> None:
        self.saved_requests.append(purchase_request)


def valid_payload() -> dict:
    return {
        "title": "Compra de computador",
        "description": "Computador para el equipo de desarrollo",
        "amount": 5000000,
        "requester_name": "Pablo Duque",
        "approvers": [
            {"name": "Juan Perez", "email": "juan@email.com"},
            {"name": "Maria Lopez", "email": "maria@email.com"},
            {"name": "Carlos Ruiz", "email": "carlos@email.com"},
        ],
    }


def make_client(repository: FakeRequestRepository) -> TestClient:
    app.dependency_overrides[get_repository] = lambda: repository
    return TestClient(app)


def test_create_purchase_request_successfully() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Compra de computador"
    assert body["description"] == "Computador para el equipo de desarrollo"
    assert body["amount"] == 5000000
    assert body["requester_name"] == "Pablo Duque"
    assert body["status"] == "PENDING"
    assert len(body["approvers"]) == 3
    assert len(repository.saved_requests) == 1

    app.dependency_overrides.clear()


def test_amount_less_than_or_equal_zero_fails() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)
    payload = valid_payload()
    payload["amount"] = 0

    response = client.post("/api/requests", json=payload)

    assert response.status_code == 422
    assert repository.saved_requests == []

    app.dependency_overrides.clear()


def test_less_than_three_approvers_fails() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)
    payload = valid_payload()
    payload["approvers"] = payload["approvers"][:2]

    response = client.post("/api/requests", json=payload)

    assert response.status_code == 422
    assert repository.saved_requests == []

    app.dependency_overrides.clear()


def test_more_than_three_approvers_fails() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)
    payload = valid_payload()
    payload["approvers"].append({"name": "Ana Gomez", "email": "ana@email.com"})

    response = client.post("/api/requests", json=payload)

    assert response.status_code == 422
    assert repository.saved_requests == []

    app.dependency_overrides.clear()


def test_duplicate_approver_emails_fail() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)
    payload = valid_payload()
    payload["approvers"][2]["email"] = "juan@email.com"

    response = client.post("/api/requests", json=payload)

    assert response.status_code == 422
    assert repository.saved_requests == []

    app.dependency_overrides.clear()


def test_request_id_is_valid_uuid() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    UUID(response.json()["request_id"])

    app.dependency_overrides.clear()


def test_generates_exactly_three_approver_tokens() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    tokens = [approver["approver_token"] for approver in response.json()["approvers"]]
    assert len(tokens) == 3

    app.dependency_overrides.clear()


def test_approver_tokens_are_different() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    tokens = [approver["approver_token"] for approver in response.json()["approvers"]]
    assert len(tokens) == len(set(tokens))

    app.dependency_overrides.clear()


def test_request_status_starts_pending() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"

    app.dependency_overrides.clear()


def test_all_approvals_start_pending() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    statuses = [approver["status"] for approver in response.json()["approvers"]]
    assert statuses == ["PENDING", "PENDING", "PENDING"]

    app.dependency_overrides.clear()

