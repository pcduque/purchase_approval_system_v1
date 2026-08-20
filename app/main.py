from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from app.api.routes.requests import router as requests_router


app = FastAPI(title="Purchase Requests API")

app.include_router(requests_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
