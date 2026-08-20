from datetime import datetime, UTC
from uuid import uuid4

from app.models.request import ApprovalStatus, Approver, PurchaseRequest, RequestStatus
from app.repositories.base import RequestRepository
from app.schemas.request import PurchaseRequestCreate


class RequestService:
    def __init__(self, repository: RequestRepository) -> None:
        self._repository = repository

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
