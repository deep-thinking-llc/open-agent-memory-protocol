"""OAMP v1 reference backend server."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api import bulk, knowledge, user_model
from .api.errors import ErrorResponse, OampError
from .config import Settings
from .repository import SQLiteRepository
from .services import KnowledgeService, UserModelService


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or Settings()

    # ── Lifespan: initialize & tear down the repository ──

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: initialize repository
        repo = SQLiteRepository(db_path=settings.db_path)
        await repo.initialize()
        app.state.repo = repo
        app.state.knowledge_service = KnowledgeService(repo)
        app.state.user_model_service = UserModelService(repo)
        yield
        # Shutdown: close repository
        await repo.close()

    app = FastAPI(
        title="Open Agent Memory Protocol API",
        description=(
            "OAMP defines a standard format for storing, exchanging, and querying "
            "memory data between AI agents and memory backends."
        ),
        version="1.0.1",
        lifespan=lifespan,
    )

    # Store settings on app state
    app.state.settings = settings

    # Register routers
    app.include_router(knowledge.router, prefix="/v1")
    app.include_router(user_model.router, prefix="/v1")
    app.include_router(bulk.router, prefix="/v1")

    # ── Error handlers ─────────────────────────────────

    @app.exception_handler(OampError)
    async def oamp_error_handler(request, exc: OampError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.error_msg, code=exc.error_code).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(l) for l in err.get("loc", []))
            errors.append(f"{loc}: {err.get('msg', 'invalid')}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="; ".join(errors),
                code="VALIDATION_ERROR",
            ).model_dump(),
        )

    # ── Health check ───────────────────────────────────

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app