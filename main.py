from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import logging
import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AuthorizationError, DomainError, DuplicateResourceError, GenerationFailureError, GuardrailViolationError, LifecycleError, NotFoundError, UploadValidationError, UsageLimitExceededError
from app.db.session import AsyncSessionLocal
from app.integrations.object_storage import get_object_storage
from app.services.bootstrap import seed_demo_owner, seed_rbac


logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        await seed_rbac(session)
        await seed_demo_owner(session)

    worker_task: asyncio.Task | None = None
    worker_stop: asyncio.Event | None = None
    settings = get_settings()
    if settings.embed_worker_in_api:
        from app.workers.runner import run_worker_loop

        worker_stop = asyncio.Event()
        worker_task = asyncio.create_task(run_worker_loop(worker_stop), name="embed-worker-loop")
        logger.info(
            "Embedded job worker started (uploads/File Processing will run automatically). "
            "Set EMBED_WORKER_IN_API=false to disable."
        )

    try:
        yield
    finally:
        if worker_stop is not None:
            worker_stop.set()
        if worker_task is not None:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.wait_for(worker_task, timeout=5)
            logger.info("Embedded job worker stopped.")


settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Drive-File-Name"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)

storage_dir = Path(settings.object_storage_base_path)
storage_dir.mkdir(parents=True, exist_ok=True)
if settings.expose_public_storage:
    if str(settings.object_storage_provider or "local").strip().lower() == "s3":
        @app.api_route("/storage/{storage_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
        async def public_storage(storage_path: str, request: Request) -> Response:
            storage = get_object_storage()
            if request.method == "HEAD":
                if not storage.exists(storage_path):
                    raise HTTPException(status_code=404, detail="Asset not found")
                return Response(media_type=mimetypes.guess_type(storage_path)[0] or "application/octet-stream")
            try:
                content = storage.read_bytes(storage_path)
            except Exception as exc:  # noqa: BLE001 - storage providers surface backend-specific errors
                raise HTTPException(status_code=404, detail="Asset not found") from exc
            return Response(
                content,
                media_type=mimetypes.guess_type(storage_path)[0] or "application/octet-stream",
            )
    else:
        app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")


@app.get("/health", include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}


@app.exception_handler(NotFoundError)
async def not_found_handler(_, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateResourceError)
async def duplicate_resource_handler(_, exc: DuplicateResourceError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(GenerationFailureError)
async def generation_failure_handler(_, exc: GenerationFailureError):
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.reason_summary,
            "failure": exc.to_payload(),
        },
    )


@app.exception_handler(AuthorizationError)
@app.exception_handler(GuardrailViolationError)
@app.exception_handler(LifecycleError)
@app.exception_handler(UploadValidationError)
@app.exception_handler(UsageLimitExceededError)
async def business_error_handler(_, exc: DomainError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
