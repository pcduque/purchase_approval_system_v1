import secrets
from datetime import datetime, timedelta, UTC
from urllib.parse import urlencode
from uuid import uuid4

from app.models.request import ApprovalStatus, Approver, PurchaseRequest, RequestStatus
from app.repositories.base import RequestRepository
from app.schemas.request import PurchaseRequestCreate

OTP_EXPIRES_IN_SECONDS = 180


class ApprovalNotPendingError(Exception):
    pass


class OtpNotStartedError(Exception):
    pass


class InvalidOtpError(Exception):
    pass


class OtpNotValidatedError(Exception):
    pass


class RequestService:
    def __init__(self, repository: RequestRepository, approval_base_url: str) -> None:
        self._repository = repository
        self._approval_base_url = approval_base_url

    def create_request(self, payload: PurchaseRequestCreate) -> PurchaseRequest:
        purchase_request = PurchaseRequest(
            request_id=str(uuid4()),
            title=payload.title,
            description=payload.description,
            amount=payload.amount,
            requester_name=payload.requester_name,
            status=RequestStatus.PENDING,
            created_at=datetime.now(UTC).isoformat(),
            approvers=[
                Approver(
                    name=approver.name,
                    email=str(approver.email),
                    approver_token=str(uuid4()),
                    status=ApprovalStatus.PENDING,
                )
                for approver in payload.approvers
            ],
        )

        self._repository.save(purchase_request)
        return purchase_request

    def list_requests(self) -> list[PurchaseRequest]:
        return self._repository.list_requests()

    def get_request(self, request_id: str) -> PurchaseRequest | None:
        return self._repository.get_by_id(request_id)

    def start_approval(self, request_id: str, approver_token: str) -> dict | None:
        approval = self._repository.get_approval(request_id, approver_token)
        if approval is None:
            return None

        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalNotPendingError("Approval is not pending")

        otp = self._generate_otp()
        otp_expires_at = (
            datetime.now(UTC) + timedelta(seconds=OTP_EXPIRES_IN_SECONDS)
        ).isoformat()

        self._repository.update_approval_otp(
            request_id=request_id,
            approver_token=approver_token,
            otp=otp,
            otp_expires_at=otp_expires_at,
        )

        return {
            "message": "Approval flow started",
            "expires_in_seconds": OTP_EXPIRES_IN_SECONDS,
        }

    def validate_otp(
        self,
        request_id: str,
        approver_token: str,
        otp: str,
    ) -> dict | None:
        approval = self._repository.get_approval(request_id, approver_token)
        if approval is None:
            return None

        if approval.otp is None or approval.otp_expires_at is None:
            raise OtpNotStartedError("OTP flow has not started")

        if approval.otp != otp:
            raise InvalidOtpError("Invalid OTP")

        if datetime.now(UTC) > datetime.fromisoformat(approval.otp_expires_at):
            raise InvalidOtpError("Expired OTP")

        self._repository.mark_otp_validated(
            request_id=request_id,
            approver_token=approver_token,
        )

        return {
            "message": "OTP validated",
            "request_id": request_id,
            "approver_token": approver_token,
        }

    def get_approval_detail(
        self,
        request_id: str,
        approver_token: str,
    ) -> PurchaseRequest | None:
        approval = self._repository.get_approval(request_id, approver_token)
        if approval is None:
            return None

        if not approval.otp_validated:
            raise OtpNotValidatedError("OTP has not been validated")

        return self._repository.get_by_id(request_id)

    def get_mock_mail(self, request_id: str) -> list[dict] | None:
        purchase_request = self._repository.get_by_id(request_id)
        if purchase_request is None:
            return None

        return [
            {
                "to": approver.email,
                "approver_name": approver.name,
                "subject": "Solicitud de aprobación",
                "approval_link": self._build_approval_link(
                    request_id=purchase_request.request_id,
                    approver_token=approver.approver_token,
                ),
                "otp": approver.otp,
                "otp_expires_at": approver.otp_expires_at,
            }
            for approver in purchase_request.approvers
        ]

    def _generate_otp(self) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def _build_approval_link(self, request_id: str, approver_token: str) -> str:
        query_params = urlencode(
            {
                "solicitud_id": request_id,
                "approver_token": approver_token,
            }
        )
        return f"{self._approval_base_url}?{query_params}"
