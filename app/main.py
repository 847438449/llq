from __future__ import annotations

from pathlib import Path

from app.runtime import configure_windows_event_loop_policy, log_startup_diagnostics

configure_windows_event_loop_policy()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_tasks import router as task_router

app = FastAPI(title="AI Browser Agent Prototype", version="0.1.0")
app.include_router(task_router)

artifacts_dir = Path("artifacts")
artifacts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=str(artifacts_dir)), name="artifacts")


@app.on_event("startup")
async def startup_diagnostics() -> None:
    log_startup_diagnostics("app.startup")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(Path("app/web/index.html"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
