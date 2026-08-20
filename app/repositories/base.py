from typing import Protocol

from app.models.request import PurchaseRequest


class RequestRepository(Protocol):
    def save(self, purchase_request: PurchaseRequest) -> None:
        ...

    def list_requests(self) -> list[PurchaseRequest]:
        ...

    def get_by_id(self, request_id: str) -> PurchaseRequest | None:
        ...
