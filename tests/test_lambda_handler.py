from mangum import Mangum

from app.main import app
from app.lambda_handler import handler


def test_lambda_handler_can_be_imported() -> None:
    assert isinstance(handler, Mangum)


def test_lambda_handler_uses_main_fastapi_app() -> None:
    assert handler.app is app


def test_lambda_handler_removes_api_gateway_stage() -> None:
    assert handler.config["api_gateway_base_path"] == "/default"
