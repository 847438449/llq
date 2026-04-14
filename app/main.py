from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_tasks import router as task_router

app = FastAPI(title="AI Browser Agent Prototype", version="0.1.0")
app.include_router(task_router)

artifacts_dir = Path("artifacts")
artifacts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=str(artifacts_dir)), name="artifacts")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(Path("app/web/index.html"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
