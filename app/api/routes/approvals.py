from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_request_service
from app.schemas.request import (
    ApprovalDetailResponse,
    ApprovalStartRequest,
    ApprovalStartResponse,
    OtpValidationRequest,
    OtpValidationResponse,
)
from app.services.request_service import (
    ApprovalNotPendingError,
    InvalidOtpError,
    OtpNotStartedError,
    OtpNotValidatedError,
    RequestService,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/start", response_model=ApprovalStartResponse)
async def start_approval(
    payload: ApprovalStartRequest,
    service: RequestService = Depends(get_request_service),
) -> ApprovalStartResponse:
    try:
        result = service.start_approval(
            request_id=payload.request_id,
            approver_token=payload.approver_token,
        )
    except ApprovalNotPendingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval is not pending",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not start approval flow",
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found",
        )

    return ApprovalStartResponse.model_validate(result)


@router.post("/validate-otp", response_model=OtpValidationResponse)
async def validate_otp(
    payload: OtpValidationRequest,
    service: RequestService = Depends(get_request_service),
) -> OtpValidationResponse:
    try:
        result = service.validate_otp(
            request_id=payload.request_id,
            approver_token=payload.approver_token,
            otp=payload.otp,
        )
    except OtpNotStartedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP flow has not started",
        ) from exc
    except InvalidOtpError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not validate OTP",
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found",
        )

    return OtpValidationResponse.model_validate(result)


@router.get("/detail", response_model=ApprovalDetailResponse)
async def get_approval_detail(
    request_id: str = Query(...),
    approver_token: str = Query(...),
    service: RequestService = Depends(get_request_service),
) -> ApprovalDetailResponse:
    try:
        purchase_request = service.get_approval_detail(
            request_id=request_id,
            approver_token=approver_token,
        )
    except OtpNotValidatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP has not been validated",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not get approval detail",
        ) from exc

    if purchase_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found",
        )

    return ApprovalDetailResponse.model_validate(purchase_request)
