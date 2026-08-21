import secrets
from datetime import datetime, timedelta, UTC
from urllib.parse import urlencode
from uuid import uuid4

from app.models.request import ApprovalStatus, Approver, PurchaseRequest, RequestStatus
from app.repositories.base import RequestRepository
from app.repositories.s3_evidence_repository import S3EvidenceRepository
from app.services.pdf_service import PdfService
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


class ApprovalAlreadyProcessedError(Exception):
    pass


class RequestAlreadyRejectedError(Exception):
    pass


class EvidenceNotAvailableError(Exception):
    pass


class RequestService:
    def __init__(
        self,
        repository: RequestRepository,
        approval_base_url: str,
        pdf_service: PdfService,
        evidence_repository: S3EvidenceRepository,
    ) -> None:
        self._repository = repository
        self._approval_base_url = approval_base_url
        self._pdf_service = pdf_service
        self._evidence_repository = evidence_repository

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

        self._ensure_request_is_not_rejected(request_id)

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

        self._ensure_request_is_not_rejected(request_id)

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

    def approve(self, request_id: str, approver_token: str) -> dict | None:
        signed_at = self._record_approval_decision(
            request_id=request_id,
            approver_token=approver_token,
            new_status=ApprovalStatus.SIGNED,
            timestamp_field="signed_at",
        )
        if signed_at is None:
            return None
        purchase_request = self._repository.get_by_id(request_id)
        all_approvals_signed = self._all_approvals_signed(purchase_request)
        if all_approvals_signed and purchase_request is not None:
            self._complete_request_with_evidence(purchase_request)

        return {
            "message": "Approval signed",
            "request_id": request_id,
            "approver_token": approver_token,
            "status": ApprovalStatus.SIGNED.value,
            "signed_at": signed_at,
            "all_approvals_signed": all_approvals_signed,
        }

    def reject(self, request_id: str, approver_token: str) -> dict | None:
        rejected_at = self._record_approval_decision(
            request_id=request_id,
            approver_token=approver_token,
            new_status=ApprovalStatus.REJECTED,
            timestamp_field="rejected_at",
        )
        if rejected_at is None:
            return None

        return {
            "message": "Approval rejected",
            "request_id": request_id,
            "approver_token": approver_token,
            "status": ApprovalStatus.REJECTED.value,
            "rejected_at": rejected_at,
        }

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

    def get_evidence_pdf(self, request_id: str) -> bytes | None:
        purchase_request = self._repository.get_by_id(request_id)
        if purchase_request is None:
            return None

        if purchase_request.status != RequestStatus.COMPLETED:
            raise EvidenceNotAvailableError("Purchase request is not completed")

        if purchase_request.evidence_s3_key is None:
            raise EvidenceNotAvailableError("Purchase request has no evidence PDF")

        return self._evidence_repository.get_pdf(purchase_request.evidence_s3_key)

    def _generate_otp(self) -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    def _record_approval_decision(
        self,
        request_id: str,
        approver_token: str,
        new_status: ApprovalStatus,
        timestamp_field: str,
    ) -> str | None:
        approval = self._repository.get_approval(request_id, approver_token)
        if approval is None:
            return None

        self._ensure_request_is_not_rejected(request_id)

        if not approval.otp_validated:
            raise OtpNotValidatedError("OTP has not been validated")

        if approval.status != ApprovalStatus.PENDING:
            raise ApprovalAlreadyProcessedError("Approval is not pending")

        timestamp = datetime.now(UTC).isoformat()
        if new_status == ApprovalStatus.REJECTED:
            self._repository.reject_approval_and_request(
                request_id=request_id,
                approver_token=approver_token,
                rejected_at=timestamp,
            )
        else:
            self._repository.update_approval_decision(
                request_id=request_id,
                approver_token=approver_token,
                status=new_status.value,
                timestamp_field=timestamp_field,
                timestamp=timestamp,
            )
        return timestamp

    def _ensure_request_is_not_rejected(self, request_id: str) -> None:
        purchase_request = self._repository.get_by_id(request_id)
        if purchase_request is not None and purchase_request.status == RequestStatus.REJECTED:
            raise RequestAlreadyRejectedError("Request is already rejected")

    def _all_approvals_signed(self, purchase_request: PurchaseRequest | None) -> bool:
        if purchase_request is None:
            return False

        return all(
            approver.status == ApprovalStatus.SIGNED
            for approver in purchase_request.approvers
        )

    def _complete_request_with_evidence(self, purchase_request: PurchaseRequest) -> None:
        if purchase_request.status == RequestStatus.COMPLETED:
            return

        evidence_s3_key = f"evidence/{purchase_request.request_id}.pdf"
        pdf_bytes = self._pdf_service.generate_evidence(purchase_request)
        self._evidence_repository.upload_pdf(evidence_s3_key, pdf_bytes)
        self._repository.complete_request(
            request_id=purchase_request.request_id,
            evidence_s3_key=evidence_s3_key,
        )

    def _build_approval_link(self, request_id: str, approver_token: str) -> str:
        query_params = urlencode(
            {
                "solicitud_id": request_id,
                "approver_token": approver_token,
            }
        )
        return f"{self._approval_base_url}?{query_params}"
