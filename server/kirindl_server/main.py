from __future__ import annotations

import hmac
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Deque

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .jobs import TaskManager, TaskStorageError
from .models import CreateTaskRequest
from .security import UnsafeURLError, validate_public_http_url
from .turnstile import (
    TurnstileUnavailableError,
    TurnstileVerificationError,
    verify_turnstile_token,
)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DATA_DIR = Path(os.getenv("KIRINDL_DATA_DIR", "/tmp/kirindl-web-downloads"))
MAX_WORKERS = int(os.getenv("KIRINDL_MAX_WORKERS", "2"))
MAX_ACTIVE_TASKS = int(os.getenv("KIRINDL_MAX_ACTIVE_TASKS", "3"))
MAX_DOWNLOAD_BYTES = int(os.getenv("KIRINDL_MAX_DOWNLOAD_BYTES", str(2 * 1024 * 1024 * 1024)))
MIN_FREE_DISK_BYTES = int(os.getenv("KIRINDL_MIN_FREE_DISK_BYTES", str(512 * 1024 * 1024)))
TASK_TIMEOUT_SECONDS = int(os.getenv("KIRINDL_TASK_TIMEOUT_SECONDS", "3600"))
RETENTION_SECONDS = int(os.getenv("KIRINDL_RETENTION_SECONDS", str(24 * 60 * 60)))
CLEANUP_INTERVAL_SECONDS = int(os.getenv("KIRINDL_CLEANUP_INTERVAL_SECONDS", "300"))
API_TOKEN = os.getenv("KIRINDL_API_TOKEN", "").strip()
TURNSTILE_REQUIRED = _env_bool("KIRINDL_REQUIRE_TURNSTILE", False)
TURNSTILE_SECRET = os.getenv("KIRINDL_TURNSTILE_SECRET", "").strip()
TURNSTILE_HOSTNAMES = {
    item.strip().lower().rstrip(".")
    for item in os.getenv(
        "KIRINDL_TURNSTILE_HOSTNAMES",
        "lanzkila.github.io",
    ).split(",")
    if item.strip()
}
ALLOWED_ORIGINS = [
    item.strip()
    for item in os.getenv(
        "KIRINDL_ALLOWED_ORIGINS",
        "https://lanzkila.github.io,http://127.0.0.1:4173,http://localhost:4173",
    ).split(",")
    if item.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.task_manager = TaskManager(
        data_dir=DATA_DIR,
        max_workers=MAX_WORKERS,
        max_active_tasks=MAX_ACTIVE_TASKS,
        max_download_bytes=MAX_DOWNLOAD_BYTES,
        task_timeout_seconds=TASK_TIMEOUT_SECONDS,
        retention_seconds=RETENTION_SECONDS,
        cleanup_interval_seconds=CLEANUP_INTERVAL_SECONDS,
        minimum_free_bytes=MIN_FREE_DISK_BYTES,
    )
    yield
    app.state.task_manager.close()


app = FastAPI(
    title="KirinDL Web Engine API",
    version="0.3.0",
    description="Server-side yt-dlp and gallery-dl adapters for the KirinDL Web frontend.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def get_manager(request: Request) -> TaskManager:
    return request.app.state.task_manager


def verify_api_token(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN:
        return
    supplied = authorization or ""
    if not hmac.compare_digest(supplied, f"Bearer {API_TOKEN}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API authentication required.")


def verify_download_challenge(body: CreateTaskRequest) -> None:
    if not TURNSTILE_SECRET:
        if TURNSTILE_REQUIRED:
            raise HTTPException(
                status_code=503,
                detail="Download security verification is not configured on the backend yet.",
            )
        if body.challenge_token:
            raise HTTPException(status_code=400, detail="The security challenge is not enabled on this server.")
        return
    if not body.challenge_token:
        raise HTTPException(status_code=400, detail="Complete the security check before downloading.")
    try:
        verify_turnstile_token(
            body.challenge_token,
            TURNSTILE_SECRET,
            TURNSTILE_HOSTNAMES,
            expected_action="download",
        )
    except TurnstileUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except TurnstileVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


_request_times: dict[str, Deque[float]] = defaultdict(deque)
_last_rate_limit_prune = 0.0


def rate_limit(request: Request) -> None:
    global _last_rate_limit_prune
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()

    # Bound memory use when many distinct client addresses hit task creation.
    if now - _last_rate_limit_prune >= 60.0:
        for host, timestamps in list(_request_times.items()):
            while timestamps and now - timestamps[0] > 60.0:
                timestamps.popleft()
            if not timestamps:
                _request_times.pop(host, None)
        _last_rate_limit_prune = now

    timestamps = _request_times[client]
    while timestamps and now - timestamps[0] > 60.0:
        timestamps.popleft()
    if len(timestamps) >= 5:
        raise HTTPException(status_code=429, detail="Too many download requests. Please wait and try again.")
    timestamps.append(now)


@app.get("/api/v1/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "kirindl-web-engine", "api_version": "v1"}


@app.post("/api/v1/tasks", status_code=status.HTTP_202_ACCEPTED)
def create_task(
    body: CreateTaskRequest,
    manager: TaskManager = Depends(get_manager),
    _: None = Depends(verify_api_token),
    __: None = Depends(rate_limit),
) -> dict[str, object]:
    verify_download_challenge(body)
    try:
        safe_url = validate_public_http_url(body.url)
    except UnsafeURLError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        return manager.create(safe_url, body.engine)
    except TaskStorageError as exc:
        raise HTTPException(status_code=507, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@app.get("/api/v1/tasks/{task_id}")
def get_task(
    task_id: str,
    manager: TaskManager = Depends(get_manager),
    _: None = Depends(verify_api_token),
) -> dict[str, object]:
    task = manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Download task not found.")
    return task


@app.delete("/api/v1/tasks/{task_id}")
def cancel_task(
    task_id: str,
    manager: TaskManager = Depends(get_manager),
    _: None = Depends(verify_api_token),
) -> dict[str, object]:
    task = manager.cancel(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Download task not found.")
    return task


@app.get("/api/v1/tasks/{task_id}/download")
def download_task(
    task_id: str,
    manager: TaskManager = Depends(get_manager),
    _: None = Depends(verify_api_token),
) -> FileResponse:
    result = manager.get_download_path(task_id)
    if not result:
        raise HTTPException(status_code=409, detail="The output file is not ready or has expired.")
    path, filename = result
    media_type = "application/zip" if path.suffix.lower() == ".zip" else "application/octet-stream"
    return FileResponse(path=path, filename=filename, media_type=media_type)
