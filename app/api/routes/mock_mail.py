from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_request_service
from app.schemas.request import MockMailResponse
from app.services.request_service import RequestService

router = APIRouter(tags=["mock-mail"])


@router.get("/mock-mail", response_model=list[MockMailResponse])
async def get_mock_mail(
    request_id: str = Query(...),
    service: RequestService = Depends(get_request_service),
) -> list[MockMailResponse]:
    try:
        mock_mails = service.get_mock_mail(request_id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not get mock mail",
        ) from exc

    if mock_mails is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase request not found",
        )

    return [MockMailResponse.model_validate(mock_mail) for mock_mail in mock_mails]
