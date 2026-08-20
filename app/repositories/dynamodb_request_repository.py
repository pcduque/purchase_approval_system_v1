from decimal import Decimal

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

from app.core.config import Settings
from app.models.request import ApprovalStatus, Approver, PurchaseRequest, RequestStatus


class DynamoDBRequestRepository:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client("dynamodb")
        self._serializer = TypeSerializer()
        self._deserializer = TypeDeserializer()

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

    def list_requests(self) -> list[PurchaseRequest]:
        try:
            response = self._client.scan(TableName=self._settings.requests_table_name)
        except ClientError as exc:
            raise RuntimeError("DynamoDB could not list purchase requests") from exc

        items = response.get("Items", [])
        return [
            self._build_purchase_request(self._deserialize_item(item), approvers=[])
            for item in items
        ]

    def get_by_id(self, request_id: str) -> PurchaseRequest | None:
        try:
            request_response = self._client.get_item(
                TableName=self._settings.requests_table_name,
                Key=self._serialize_item({"request_id": request_id}),
            )
        except ClientError as exc:
            raise RuntimeError("DynamoDB could not get purchase request") from exc

        request_item = request_response.get("Item")
        if request_item is None:
            return None

        try:
            approvals_response = self._client.query(
                TableName=self._settings.approvals_table_name,
                KeyConditionExpression="request_id = :request_id",
                ExpressionAttributeValues=self._serialize_item(
                    {":request_id": request_id}
                ),
            )
        except ClientError as exc:
            raise RuntimeError("DynamoDB could not get purchase approvals") from exc

        approvers = [
            self._build_approver(self._deserialize_item(item))
            for item in approvals_response.get("Items", [])
        ]

        return self._build_purchase_request(
            self._deserialize_item(request_item),
            approvers=approvers,
        )

    def _serialize_item(self, item: dict) -> dict:
        return {key: self._serializer.serialize(value) for key, value in item.items()}

    def _deserialize_item(self, item: dict) -> dict:
        return {
            key: self._normalize_number(self._deserializer.deserialize(value))
            for key, value in item.items()
        }

    def _normalize_number(self, value):
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _build_purchase_request(
        self,
        item: dict,
        approvers: list[Approver],
    ) -> PurchaseRequest:
        return PurchaseRequest(
            request_id=item["request_id"],
            title=item["title"],
            description=item["description"],
            amount=item["amount"],
            requester_name=item["requester_name"],
            status=RequestStatus(item["status"]),
            created_at=item["created_at"],
            approvers=approvers,
        )

    def _build_approver(self, item: dict) -> Approver:
        return Approver(
            name=item["name"],
            email=item["email"],
            approver_token=item["approver_token"],
            status=ApprovalStatus(item["status"]),
        )
