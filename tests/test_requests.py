from datetime import datetime, UTC
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

    def get_approval(self, request_id: str, approver_token: str) -> Approver | None:
        purchase_request = self.get_by_id(request_id)
        if purchase_request is None:
            return None

        for approver in purchase_request.approvers:
            if approver.approver_token == approver_token:
                return approver
        return None

    def update_approval_otp(
        self,
        request_id: str,
        approver_token: str,
        otp: str,
        otp_expires_at: str,
    ) -> None:
        approval = self.get_approval(request_id, approver_token)
        if approval is None:
            return

        object.__setattr__(approval, "otp", otp)
        object.__setattr__(approval, "otp_expires_at", otp_expires_at)
        object.__setattr__(approval, "otp_validated", False)

    def mark_otp_validated(self, request_id: str, approver_token: str) -> None:
        approval = self.get_approval(request_id, approver_token)
        if approval is None:
            return

        object.__setattr__(approval, "otp_validated", True)


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


def existing_purchase_request(
    request_id: str = "request-1",
    approval_status: ApprovalStatus = ApprovalStatus.PENDING,
    include_otp: bool = False,
    otp_expired: bool = False,
    otp_validated: bool = False,
) -> PurchaseRequest:
    if include_otp and otp_expired:
        otp_expires_at = "2020-01-01T00:00:00+00:00"
    elif include_otp:
        otp_expires_at = "2099-01-01T00:00:00+00:00"
    else:
        otp_expires_at = None
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
                status=approval_status,
                otp="111111" if include_otp else None,
                otp_expires_at=otp_expires_at,
                otp_validated=otp_validated,
            ),
            Approver(
                name="Maria Lopez",
                email="maria@email.com",
                approver_token=f"{request_id}-token-2",
                status=approval_status,
                otp="222222" if include_otp else None,
                otp_expires_at=otp_expires_at,
                otp_validated=otp_validated,
            ),
            Approver(
                name="Carlos Ruiz",
                email="carlos@email.com",
                approver_token=f"{request_id}-token-3",
                status=approval_status,
                otp="333333" if include_otp else None,
                otp_expires_at=otp_expires_at,
                otp_validated=otp_validated,
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


def test_create_purchase_request_does_not_generate_otp() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    otps = [approver.otp for approver in repository.saved_requests[0].approvers]
    assert otps == [None, None, None]

    app.dependency_overrides.clear()


def test_create_purchase_request_does_not_generate_otp_expiration() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    expirations = [
        approver.otp_expires_at
        for approver in repository.saved_requests[0].approvers
    ]
    assert expirations == [None, None, None]

    app.dependency_overrides.clear()


def test_approver_tokens_remain_different_without_otp_generation() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.post("/api/requests", json=valid_payload())

    assert response.status_code == 201
    tokens = [
        approver.approver_token
        for approver in repository.saved_requests[0].approvers
    ]
    assert len(tokens) == len(set(tokens))

    app.dependency_overrides.clear()


def test_request_otp_generates_six_digit_otp() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    approval = repository.get_approval("request-1", "request-1-token-1")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Approval flow started",
        "expires_in_seconds": 180,
    }
    assert approval is not None
    assert approval.otp is not None
    assert len(approval.otp) == 6

    app.dependency_overrides.clear()


def test_request_otp_generates_numeric_otp() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    approval = repository.get_approval("request-1", "request-1-token-1")
    assert response.status_code == 200
    assert approval is not None
    assert approval.otp is not None
    assert approval.otp.isdigit()

    app.dependency_overrides.clear()


def test_request_otp_sets_expiration_near_three_minutes() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)
    before_request = datetime.now(UTC)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    after_request = datetime.now(UTC)
    approval = repository.get_approval("request-1", "request-1-token-1")
    assert response.status_code == 200
    assert approval is not None
    assert approval.otp_expires_at is not None
    expires_at = datetime.fromisoformat(approval.otp_expires_at)
    assert before_request.timestamp() + 180 <= expires_at.timestamp()
    assert expires_at.timestamp() <= after_request.timestamp() + 180

    app.dependency_overrides.clear()


def test_start_sets_otp_validated_false() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(
        existing_purchase_request(include_otp=True, otp_validated=True)
    )
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    approval = repository.get_approval("request-1", "request-1-token-1")
    assert response.status_code == 200
    assert approval is not None
    assert approval.otp_validated is False

    app.dependency_overrides.clear()


def test_request_otp_updates_only_requested_approval() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    requested = repository.get_approval("request-1", "request-1-token-1")
    second = repository.get_approval("request-1", "request-1-token-2")
    third = repository.get_approval("request-1", "request-1-token-3")
    assert response.status_code == 200
    assert requested is not None
    assert requested.otp is not None
    assert second is not None
    assert second.otp is None
    assert third is not None
    assert third.otp is None

    app.dependency_overrides.clear()


def test_second_approver_does_not_receive_otp_until_requested() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    second = repository.get_approval("request-1", "request-1-token-2")
    assert response.status_code == 200
    assert second is not None
    assert second.otp is None
    assert second.otp_expires_at is None

    app.dependency_overrides.clear()


def test_request_otp_for_missing_approval_returns_404() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "missing-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Approval not found"

    app.dependency_overrides.clear()


def test_request_otp_for_non_pending_approval_returns_409() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(
        existing_purchase_request(approval_status=ApprovalStatus.SIGNED)
    )
    client = make_client(repository)

    response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Approval is not pending"

    app.dependency_overrides.clear()


def test_validate_otp_success_returns_expected_response() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request(include_otp=True))
    client = make_client(repository)

    response = client.post(
        "/api/approvals/validate-otp",
        json={
            "request_id": "request-1",
            "approver_token": "request-1-token-1",
            "otp": "111111",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "OTP validated",
        "request_id": "request-1",
        "approver_token": "request-1-token-1",
    }

    app.dependency_overrides.clear()


def test_validate_otp_incorrect_returns_401() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request(include_otp=True))
    client = make_client(repository)

    response = client.post(
        "/api/approvals/validate-otp",
        json={
            "request_id": "request-1",
            "approver_token": "request-1-token-1",
            "otp": "999999",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired OTP"

    app.dependency_overrides.clear()


def test_validate_otp_expired_returns_401() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request(include_otp=True, otp_expired=True))
    client = make_client(repository)

    response = client.post(
        "/api/approvals/validate-otp",
        json={
            "request_id": "request-1",
            "approver_token": "request-1-token-1",
            "otp": "111111",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired OTP"

    app.dependency_overrides.clear()


def test_validate_otp_without_start_returns_400() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.post(
        "/api/approvals/validate-otp",
        json={
            "request_id": "request-1",
            "approver_token": "request-1-token-1",
            "otp": "111111",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "OTP flow has not started"

    app.dependency_overrides.clear()


def test_validate_otp_marks_otp_validated_true() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request(include_otp=True))
    client = make_client(repository)

    response = client.post(
        "/api/approvals/validate-otp",
        json={
            "request_id": "request-1",
            "approver_token": "request-1-token-1",
            "otp": "111111",
        },
    )

    approval = repository.get_approval("request-1", "request-1-token-1")
    assert response.status_code == 200
    assert approval is not None
    assert approval.otp_validated is True

    app.dependency_overrides.clear()


def test_approval_detail_works_when_otp_validated() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(
        existing_purchase_request(include_otp=True, otp_validated=True)
    )
    client = make_client(repository)

    response = client.get(
        "/api/approvals/detail",
        params={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    assert response.status_code == 200
    assert response.json()["request_id"] == "request-1"
    assert response.json()["title"] == "Compra de computador"

    app.dependency_overrides.clear()


def test_approval_detail_returns_403_when_otp_not_validated() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request(include_otp=True))
    client = make_client(repository)

    response = client.get(
        "/api/approvals/detail",
        params={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "OTP has not been validated"

    app.dependency_overrides.clear()


def test_approval_detail_does_not_return_otp() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(
        existing_purchase_request(include_otp=True, otp_validated=True)
    )
    client = make_client(repository)

    response = client.get(
        "/api/approvals/detail",
        params={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    assert response.status_code == 200
    assert "otp" not in response.json()

    app.dependency_overrides.clear()


def test_approval_detail_does_not_return_otp_expires_at() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(
        existing_purchase_request(include_otp=True, otp_validated=True)
    )
    client = make_client(repository)

    response = client.get(
        "/api/approvals/detail",
        params={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )

    assert response.status_code == 200
    assert "otp_expires_at" not in response.json()

    app.dependency_overrides.clear()


def test_mock_mail_returns_exactly_three_emails() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/mock-mail", params={"request_id": "request-1"})

    assert response.status_code == 200
    assert len(response.json()) == 3

    app.dependency_overrides.clear()


def test_mock_mail_returns_correct_emails() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/mock-mail", params={"request_id": "request-1"})

    assert response.status_code == 200
    emails = [mock_mail["to"] for mock_mail in response.json()]
    assert emails == ["juan@email.com", "maria@email.com", "carlos@email.com"]

    app.dependency_overrides.clear()


def test_mock_mail_approval_links_include_request_id() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/mock-mail", params={"request_id": "request-1"})

    assert response.status_code == 200
    links = [mock_mail["approval_link"] for mock_mail in response.json()]
    assert all("solicitud_id=request-1" in link for link in links)

    app.dependency_overrides.clear()


def test_mock_mail_approval_links_include_approver_tokens() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/mock-mail", params={"request_id": "request-1"})

    assert response.status_code == 200
    links = [mock_mail["approval_link"] for mock_mail in response.json()]
    assert "approver_token=request-1-token-1" in links[0]
    assert "approver_token=request-1-token-2" in links[1]
    assert "approver_token=request-1-token-3" in links[2]

    app.dependency_overrides.clear()


def test_mock_mail_before_request_otp_does_not_assume_otp_exists() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    response = client.get("/mock-mail", params={"request_id": "request-1"})

    assert response.status_code == 200
    mock_mails = response.json()
    assert [mock_mail["otp"] for mock_mail in mock_mails] == [None, None, None]
    assert [mock_mail["otp_expires_at"] for mock_mail in mock_mails] == [
        None,
        None,
        None,
    ]

    app.dependency_overrides.clear()


def test_mock_mail_after_request_otp_shows_otp_for_requested_approver() -> None:
    repository = FakeRequestRepository()
    repository.requests.append(existing_purchase_request())
    client = make_client(repository)

    otp_response = client.post(
        "/api/approvals/start",
        json={"request_id": "request-1", "approver_token": "request-1-token-1"},
    )
    mock_mail_response = client.get("/mock-mail", params={"request_id": "request-1"})

    assert otp_response.status_code == 200
    assert mock_mail_response.status_code == 200
    mock_mails = mock_mail_response.json()
    assert mock_mails[0]["otp"] is not None
    assert mock_mails[0]["otp_expires_at"] is not None
    assert mock_mails[1]["otp"] is None
    assert mock_mails[1]["otp_expires_at"] is None
    assert mock_mails[2]["otp"] is None
    assert mock_mails[2]["otp_expires_at"] is None

    app.dependency_overrides.clear()


def test_mock_mail_missing_request_id_returns_404() -> None:
    repository = FakeRequestRepository()
    client = make_client(repository)

    response = client.get("/mock-mail", params={"request_id": "missing-request"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Purchase request not found"

    app.dependency_overrides.clear()
