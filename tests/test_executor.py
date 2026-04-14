from __future__ import annotations

import pytest

from app.agent.executor import TaskExecutor
from app.schemas.task import PlannedStep


class DummyPage:
    def __init__(self) -> None:
        self.url = "https://example.com"


class DummyPlanner:
    def __init__(self, steps: list[PlannedStep]) -> None:
        self.steps = steps
        self.idx = 0

    def next_action(self, **kwargs):
        step = self.steps[min(self.idx, len(self.steps) - 1)]
        self.idx += 1
        return step, {
            "planner_input_summary": "input",
            "planner_raw_output": "raw",
            "validated_action": step.model_dump_json(),
            "planner_reasoning_summary": "summary",
            "past_experience_used": "none",
        }


@pytest.mark.asyncio
async def test_repeated_action_loop_prevention(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = TaskExecutor()
    page = DummyPage()

    async def fake_start(self):
        return page

    async def fake_close(self):
        return None

    async def fake_context(_page):
        return {"url": page.url, "title": "t", "summary": "s"}

    async def fake_open_url(_page, _url):
        return {"ok": True}

    async def fake_screenshot(*args, **kwargs):
        return {"path": "x.png"}

    monkeypatch.setattr("app.agent.executor.BrowserManager.start", fake_start)
    monkeypatch.setattr("app.agent.executor.BrowserManager.close", fake_close)
    monkeypatch.setattr("app.agent.executor.extract_page_context", fake_context)
    monkeypatch.setattr("app.agent.executor.open_url", fake_open_url)
    monkeypatch.setattr("app.agent.executor.take_screenshot", fake_screenshot)

    planner = DummyPlanner([
        PlannedStep(action="open_url", params={"url": "https://a.com"}),
        PlannedStep(action="open_url", params={"url": "https://a.com"}),
        PlannedStep(action="open_url", params={"url": "https://a.com"}),
    ])

    response = await executor.run("go", planner)
    assert len(response.steps) <= 2


@pytest.mark.asyncio
async def test_failed_action_twice_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = TaskExecutor()
    page = DummyPage()

    async def fake_start(self):
        return page

    async def fake_close(self):
        return None

    async def fake_context(_page):
        return {"url": page.url, "title": "t", "summary": "s"}

    async def fake_open_url(_page, _url):
        raise RuntimeError("boom")

    async def fake_screenshot(*args, **kwargs):
        return {"path": "x.png"}

    monkeypatch.setattr("app.agent.executor.BrowserManager.start", fake_start)
    monkeypatch.setattr("app.agent.executor.BrowserManager.close", fake_close)
    monkeypatch.setattr("app.agent.executor.extract_page_context", fake_context)
    monkeypatch.setattr("app.agent.executor.open_url", fake_open_url)
    monkeypatch.setattr("app.agent.executor.take_screenshot", fake_screenshot)

    planner = DummyPlanner([PlannedStep(action="open_url", params={"url": "https://a.com"})])
    response = await executor.run("go", planner)

    assert len(response.steps) == 2
    assert response.steps[-1].success is False


@pytest.mark.asyncio
async def test_take_screenshot_stops_iteration(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = TaskExecutor()
    page = DummyPage()

    async def fake_start(self):
        return page

    async def fake_close(self):
        return None

    async def fake_context(_page):
        return {"url": page.url, "title": "t", "summary": "s"}

    async def fake_screenshot(*args, **kwargs):
        return {"path": "x.png"}

    monkeypatch.setattr("app.agent.executor.BrowserManager.start", fake_start)
    monkeypatch.setattr("app.agent.executor.BrowserManager.close", fake_close)
    monkeypatch.setattr("app.agent.executor.extract_page_context", fake_context)
    monkeypatch.setattr("app.agent.executor.take_screenshot", fake_screenshot)

    planner = DummyPlanner([PlannedStep(action="take_screenshot", params={"name": "final"})])
    response = await executor.run("go", planner)
    assert len(response.steps) == 1
