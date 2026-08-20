from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


NonEmptyString = Annotated[str, Field(min_length=1)]


class ApproverCreate(BaseModel):
    name: NonEmptyString
    email: EmailStr

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class PurchaseRequestCreate(BaseModel):
    title: NonEmptyString
    description: NonEmptyString
    amount: float = Field(gt=0)
    requester_name: NonEmptyString
    approvers: list[ApproverCreate] = Field(min_length=3, max_length=3)

    @field_validator("title", "description", "requester_name", mode="before")
    @classmethod
    def strip_text_fields(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def approver_emails_must_be_unique(self) -> "PurchaseRequestCreate":
        emails = [approver.email.lower() for approver in self.approvers]
        if len(emails) != len(set(emails)):
            raise ValueError("approver emails must be different")
        return self


class ApproverResponse(BaseModel):
    name: str
    email: EmailStr
    approver_token: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class PurchaseRequestSummaryResponse(BaseModel):
    request_id: str
    title: str
    description: str
    amount: float
    requester_name: str
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class PurchaseRequestResponse(BaseModel):
    request_id: str
    title: str
    description: str
    amount: float
    requester_name: str
    status: str
    created_at: str
    approvers: list[ApproverResponse]

    model_config = ConfigDict(from_attributes=True)


class MockMailResponse(BaseModel):
    to: EmailStr
    approver_name: str
    subject: str
    approval_link: str
    otp: str | None = None
    otp_expires_at: str | None = None


class ApprovalStartRequest(BaseModel):
    request_id: str
    approver_token: str


class ApprovalStartResponse(BaseModel):
    message: str
    expires_in_seconds: int


class OtpValidationRequest(BaseModel):
    request_id: str
    approver_token: str
    otp: str


class OtpValidationResponse(BaseModel):
    message: str
    request_id: str
    approver_token: str


class ApprovalDetailResponse(BaseModel):
    request_id: str
    title: str
    description: str
    amount: float
    requester_name: str
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
