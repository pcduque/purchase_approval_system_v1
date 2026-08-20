from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_request_service
from app.schemas.request import (
    PurchaseRequestCreate,
    PurchaseRequestResponse,
    PurchaseRequestSummaryResponse,
)
from app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("", response_model=list[PurchaseRequestSummaryResponse])
async def list_purchase_requests(
    service: RequestService = Depends(get_request_service),
) -> list[PurchaseRequestSummaryResponse]:
    try:
        purchase_requests = service.list_requests()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not list purchase requests",
        ) from exc

    return [
        PurchaseRequestSummaryResponse.model_validate(purchase_request)
        for purchase_request in purchase_requests
    ]


@router.get("/{request_id}", response_model=PurchaseRequestResponse)
async def get_purchase_request(
    request_id: str,
    service: RequestService = Depends(get_request_service),
) -> PurchaseRequestResponse:
    try:
        purchase_request = service.get_request(request_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not get purchase request",
        ) from exc

    if purchase_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase request not found",
        )

    return PurchaseRequestResponse.model_validate(purchase_request)


@router.post(
    "",
    response_model=PurchaseRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_purchase_request(
    payload: PurchaseRequestCreate,
    service: RequestService = Depends(get_request_service),
) -> PurchaseRequestResponse:
    try:
        purchase_request = service.create_request(payload)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save purchase request",
        ) from exc

    return PurchaseRequestResponse.model_validate(purchase_request)
