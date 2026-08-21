from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

load_dotenv()

from app.api.routes.requests import router as requests_router
from app.api.routes.mock_mail import router as mock_mail_router
from app.api.routes.approvals import router as approvals_router
from app.core.config import Settings


settings = Settings()

app = FastAPI(
    title="Purchase Requests API",
    root_path=settings.root_path,
    docs_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requests_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(mock_mail_router)


def build_docs_openapi_url(root_path: str, openapi_url: str) -> str:
    normalized_root_path = root_path.rstrip("/")
    normalized_openapi_url = openapi_url if openapi_url.startswith("/") else f"/{openapi_url}"
    return f"{normalized_root_path}{normalized_openapi_url}"


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=build_docs_openapi_url(app.root_path, app.openapi_url),
        title=f"{app.title} - Swagger UI",
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
