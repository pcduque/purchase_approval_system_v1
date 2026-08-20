from functools import lru_cache

from fastapi import Depends

from app.core.config import Settings
from app.repositories.base import RequestRepository
from app.repositories.dynamodb_request_repository import DynamoDBRequestRepository
from app.services.request_service import RequestService


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_repository(settings: Settings = Depends(get_settings)) -> RequestRepository:
    return DynamoDBRequestRepository(settings=settings)


def get_request_service(
    repository: RequestRepository = Depends(get_repository),
) -> RequestService:
    return RequestService(repository=repository)
