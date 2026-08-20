from uuid import UUID
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.main import app
from app.models.request import ApprovalStatus, Approver, PurchaseRequest, RequestStatus


class FakeRequestRepository:
    def __init__(self) -> None:
        self.saved_requests: list[PurchaseRequest] = []
        self.requests: list[PurchaseRequest] = []

    def save(self, purchase_request: PurchaseRequest) -> None:
        self.saved_requests.append(purchase_request)
        self.requests.append(purchase_request)

    def list_requests(self) -> list[PurchaseRequest]:
        return self.requests

    def get_by_id(self, request_id: str) -> PurchaseRequest | None:
        for purchase_request in self.requests:
            if purchase_request.request_id == request_id:
                return purchase_request
        return None


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


def existing_purchase_request(request_id: str = "request-1") -> PurchaseRequest:
    return PurchaseRequest(
        request_id=request_id,
        title="Compra de computador",
        description="Computador para el equipo de desarrollo",
        amount=5000000,
        requester_name="Pablo Duque",
        status=RequestStatus.PENDING,
        created_at="2026-08-19T15:00:00+00:00",
        approvers=[
            Approver(
                name="Juan Perez",
                email="juan@email.com",
                approver_token=f"{request_id}-token-1",
                status=ApprovalStatus.PENDING,
            ),
            Approver(
                name="Maria Lopez",
                email="maria@email.com",
                approver_token=f"{request_id}-token-2",
                status=ApprovalStatus.PENDING,
            ),
            Approver(
                name="Carlos Ruiz",
                email="carlos@email.com",
                approver_token=f"{request_id}-token-3",
                status=ApprovalStatus.PENDING,
            ),
        ],
    )


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


def test_list_purchase_requests_returns_requests() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/api/requests")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["request_id"] == "request-1"
    assert body[0]["title"] == "Compra de computador"
    assert "approvers" not in body[0]

    app.dependency_overrides.clear()


def test_get_purchase_request_by_id_returns_existing_request() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/api/requests/request-1")

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == "request-1"
    assert body["title"] == "Compra de computador"
    assert body["requester_name"] == "Pablo Duque"

    app.dependency_overrides.clear()


def test_get_purchase_request_by_id_includes_three_approvers() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/api/requests/request-1")

    assert response.status_code == 200
    assert len(response.json()["approvers"]) == 3

    app.dependency_overrides.clear()


def test_get_missing_purchase_request_returns_404() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.get("/api/requests/missing-request")

    assert response.status_code == 404
    assert response.json()["detail"] == "Purchase request not found"

    app.dependency_overrides.clear()


def test_get_purchase_request_returns_approvals_for_requested_request_id() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request(request_id="request-1"))
    repository.requests.append(existing_purchase_request(request_id="request-2"))
    client = make_client(repository)

    response = client.get("/api/requests/request-2")

    assert response.status_code == 200
    assert response.json()["request_id"] == "request-2"
    tokens = [approver["approver_token"] for approver in response.json()["approvers"]]
    assert tokens == ["request-2-token-1", "request-2-token-2", "request-2-token-3"]

    app.dependency_overrides.clear()
