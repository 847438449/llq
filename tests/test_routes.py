from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.main import app


def test_route_blocks_dangerous_task() -> None:
    client = TestClient(app)
    response = client.post("/api/tasks/run", json={"task": "login to my bank"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["blocked"] is True
    assert payload["steps"] == []


def test_debug_mode_response_fields(monkeypatch) -> None:
    from app.api import routes_tasks

    async def fake_run(task, planner, debug=False, initial_page_context=None):
        from app.schemas.task import TaskDebugInfo, TaskRunResponse

        return TaskRunResponse(
            task=task,
            blocked=False,
            steps=[],
            extracted_data={},
            debug=TaskDebugInfo(
                task_id="t1",
                matched_skill="generic_web",
                planner_reasoning_summary="summary",
                past_experience_used="none",
                step_traces=[],
            ) if debug else None,
        )

    monkeypatch.setattr(routes_tasks.executor, "run", fake_run)

    client = TestClient(app)
    response = client.post("/api/tasks/run", json={"task": "open docs", "debug": True})
    assert response.status_code == 200
    payload = response.json()
    assert payload["debug"]["matched_skill"] == "generic_web"


def test_web_ui_index_route() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Browser Agent" in response.text
