from typing import Protocol

from app.models.request import Approver, PurchaseRequest


class RequestRepository(Protocol):
    def save(self, purchase_request: PurchaseRequest) -> None:
        ...

    def list_requests(self) -> list[PurchaseRequest]:
        ...

    def get_by_id(self, request_id: str) -> PurchaseRequest | None:
        ...

    def get_approval(self, request_id: str, approver_token: str) -> Approver | None:
        ...

    def update_approval_otp(
        self,
        request_id: str,
        approver_token: str,
        otp: str,
        otp_expires_at: str,
    ) -> None:
        ...

    def mark_otp_validated(self, request_id: str, approver_token: str) -> None:
        ...

    def update_approval_decision(
        self,
        request_id: str,
        approver_token: str,
        status: str,
        timestamp_field: str,
        timestamp: str,
    ) -> None:
        ...

    def reject_approval_and_request(
        self,
        request_id: str,
        approver_token: str,
        rejected_at: str,
    ) -> None:
        ...

    def complete_request(self, request_id: str, evidence_s3_key: str) -> None:
        ...
