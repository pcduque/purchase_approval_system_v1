from typing import Protocol

from app.models.request import PurchaseRequest


class RequestRepository(Protocol):
    def save(self, purchase_request: PurchaseRequest) -> None:
        ...
