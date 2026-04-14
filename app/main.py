from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_tasks import router as task_router

app = FastAPI(title="AI Browser Agent Prototype", version="0.1.0")
app.include_router(task_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
