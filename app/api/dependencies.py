from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings
from app.repositories.base import RequestRepository
from app.repositories.dynamodb_request_repository import DynamoDBRequestRepository
from app.repositories.s3_evidence_repository import S3EvidenceRepository
from app.services.pdf_service import PdfService
from app.services.request_service import RequestService


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_repository(settings: Settings = Depends(get_settings)) -> RequestRepository:
    return DynamoDBRequestRepository(settings=settings)


def get_pdf_service() -> PdfService:
    return PdfService()


def get_evidence_repository(
    settings: Settings = Depends(get_settings),
) -> S3EvidenceRepository:
    return S3EvidenceRepository(bucket_name=settings.evidence_bucket_name)


def get_request_service(
    repository: RequestRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
    pdf_service: PdfService = Depends(get_pdf_service),
    evidence_repository: S3EvidenceRepository = Depends(get_evidence_repository),
) -> RequestService:
    return RequestService(
        repository=repository,
        approval_base_url=settings.approval_base_url,
        pdf_service=pdf_service,
        evidence_repository=evidence_repository,
    )
