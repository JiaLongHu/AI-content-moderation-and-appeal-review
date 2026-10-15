from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.appeals import router as appeals_router
from backend.app.api.auth import router as auth_router
from backend.app.api.contents import router as contents_router
from backend.app.api.moderation_tasks import router as moderation_tasks_router
from backend.app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="AI Content Moderation and Appeal API",
        version="0.1.0",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(appeals_router, prefix="/api/v1")
    application.include_router(contents_router, prefix="/api/v1")
    application.include_router(moderation_tasks_router, prefix="/api/v1")

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
