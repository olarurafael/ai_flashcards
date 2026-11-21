from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, decks, study

app = FastAPI(title="AI Flashcards API", docs_url="/api/docs", openapi_url="/api/openapi.json")

# Everything lives under /api: CloudFront sends /api/* to API Gateway and the
# rest to the static frontend, so both share one origin and need no CORS.
api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(decks.router)
api.include_router(study.router)


@api.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api)

if origins := get_settings().cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )
