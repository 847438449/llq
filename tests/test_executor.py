from __future__ import annotations

import pytest

from app.agent.executor import TaskExecutor
from app.schemas.task import PlannedStep


class DummyPage:
    def __init__(self) -> None:
        self.url = "https://example.com"


class DummyPlanner:
    def __init__(self, steps: list[PlannedStep], raw_output: str = "raw") -> None:
        self.steps = steps
        self.idx = 0
        self.raw_output = raw_output

    def next_action(self, **kwargs):
        step = self.steps[min(self.idx, len(self.steps) - 1)]
        self.idx += 1
        return step, {
            "planner_input_summary": "input",
            "planner_raw_output": self.raw_output,
            "validated_action": step.model_dump_json(),
            "planner_reasoning_summary": "summary",
            "past_experience_used": "none",
        }


@pytest.mark.asyncio
async def test_repeated_validated_action_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = TaskExecutor()
    page = DummyPage()

    async def fake_start(self): return page
    async def fake_close(self): return None
    async def fake_context(_): return {"url": page.url, "title": "same", "summary": "same"}
    async def fake_open_url(_, __): return {"ok": True}
    async def fake_shot(*a, **k): return {"path": "x.png"}

    monkeypatch.setattr("app.agent.executor.BrowserManager.start", fake_start)
    monkeypatch.setattr("app.agent.executor.BrowserManager.close", fake_close)
    monkeypatch.setattr("app.agent.executor.extract_page_context", fake_context)
    monkeypatch.setattr("app.agent.executor.open_url", fake_open_url)
    monkeypatch.setattr("app.agent.executor.take_screenshot", fake_shot)

    planner = DummyPlanner([PlannedStep(action="open_url", params={"url": "https://a.com"})])
    resp = await executor.run("go", planner)
    assert resp.stop_reason == "repeated_validated_action_no_progress"


@pytest.mark.asyncio
async def test_repeated_no_progress_planner_loop_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = TaskExecutor()
    page = DummyPage()

    async def fake_start(self): return page
    async def fake_close(self): return None
    async def fake_context(_): return {"url": page.url, "title": "same", "summary": "same"}
    async def fake_open_url(_, __): return {"ok": False}
    async def fake_shot(*a, **k): return {"path": "x.png"}

    monkeypatch.setattr("app.agent.executor.BrowserManager.start", fake_start)
    monkeypatch.setattr("app.agent.executor.BrowserManager.close", fake_close)
    monkeypatch.setattr("app.agent.executor.extract_page_context", fake_context)
    monkeypatch.setattr("app.agent.executor.open_url", fake_open_url)
    monkeypatch.setattr("app.agent.executor.take_screenshot", fake_shot)

    planner = DummyPlanner([PlannedStep(action="open_url", params={"url": "https://a.com"})], raw_output='{"action":"open_url"}')
    resp = await executor.run("go", planner)
    assert resp.stop_reason in {"repeated_planner_output_no_progress", "repeated_validated_action_no_progress"}


@pytest.mark.asyncio
async def test_screenshot_failure_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = TaskExecutor()
    page = DummyPage()

    async def fake_start(self): return page
    async def fake_close(self): return None
    async def fake_context(_): return {"url": page.url, "title": "t", "summary": "s"}
    async def fake_extract(_): return {"title": "t", "summary": "s"}

    async def bad_shot(*a, **k):
        raise RuntimeError("shot failed")

    monkeypatch.setattr("app.agent.executor.BrowserManager.start", fake_start)
    monkeypatch.setattr("app.agent.executor.BrowserManager.close", fake_close)
    monkeypatch.setattr("app.agent.executor.extract_page_context", fake_context)
    monkeypatch.setattr("app.agent.executor.extract_page_summary", fake_extract)
    monkeypatch.setattr("app.agent.executor.take_screenshot", bad_shot)

    planner = DummyPlanner([PlannedStep(action="extract_page_summary", params={}), PlannedStep(action="take_screenshot", params={})])
    resp = await executor.run("go", planner)
    assert resp.steps
    assert any((s.error or "").startswith("screenshot_failed") for s in resp.steps)
