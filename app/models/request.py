from dataclasses import dataclass
from enum import StrEnum


class RequestStatus(StrEnum):
    PENDING = "PENDING"
    SIGNED = "SIGNED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    SIGNED = "SIGNED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class Approver:
    name: str
    email: str
    approver_token: str
    status: ApprovalStatus


@dataclass(frozen=True)
class PurchaseRequest:
    request_id: str
    title: str
    description: str
    amount: float
    requester_name: str
    status: RequestStatus
    created_at: str
    approvers: list[Approver]
