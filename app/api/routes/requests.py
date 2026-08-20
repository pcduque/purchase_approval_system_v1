from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_request_service
from app.schemas.request import PurchaseRequestCreate, PurchaseRequestResponse
from app.services.request_service import RequestService

router = APIRouter(prefix="/requests", tags=["requests"])


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
