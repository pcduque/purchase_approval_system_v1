from decimal import Decimal

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeSerializer

from app.core.config import Settings
from app.models.request import PurchaseRequest


class DynamoDBRequestRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")
        self._serializer = TypeSerializer()

    def save(self, purchase_request: PurchaseRequest) -> None:
        request_item = {
            "request_id": purchase_request.request_id,
            "title": purchase_request.title,
            "description": purchase_request.description,
            "amount": Decimal(str(purchase_request.amount)),
            "requester_name": purchase_request.requester_name,
            "status": purchase_request.status.value,
            "created_at": purchase_request.created_at,
        }

        transact_items = [
            {
                "Put": {
                    "TableName": self._settings.requests_table_name,
                    "Item": self._serialize_item(request_item),
                }
            }
        ]

        for approver in purchase_request.approvers:
            approval_item = {
                "request_id": purchase_request.request_id,
                "approver_token": approver.approver_token,
                "name": approver.name,
                "email": approver.email,
                "status": approver.status.value,
            }
            transact_items.append(
                {
                    "Put": {
                        "TableName": self._settings.approvals_table_name,
                        "Item": self._serialize_item(approval_item),
                    }
                }
            )

        try:
            self._client.transact_write_items(TransactItems=transact_items)
        except ClientError as exc:
            raise RuntimeError("DynamoDB could not save purchase request") from exc

    def _serialize_item(self, item: dict) -> dict:
        return {key: self._serializer.serialize(value) for key, value in item.items()}
