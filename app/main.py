from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api.routes.requests import router as requests_router
from app.api.routes.mock_mail import router as mock_mail_router
from app.api.routes.approvals import router as approvals_router


app = FastAPI(title="Purchase Requests API")

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
