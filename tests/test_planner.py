from __future__ import annotations

import pytest

from app.agent.planner import RuleBasedPlanner


@pytest.fixture()
def planner() -> RuleBasedPlanner:
    return RuleBasedPlanner()


def test_validator_allows_valid_open_url(planner: RuleBasedPlanner) -> None:
    step = planner._validate_next_step({"action": "open_url", "params": {"url": "https://www.bilibili.com"}}, set())
    assert step.action == "open_url"


def test_invalid_action_falls_back_with_reason(monkeypatch: pytest.MonkeyPatch, planner: RuleBasedPlanner) -> None:
    def bad_llm(*args, **kwargs):
        raise ValueError("Unknown action: bad_action")

    monkeypatch.setattr(planner, "llm_next_action", bad_llm)
    step, debug = planner.next_action(
        task="go to bilibili",
        page_state={"url": "about:blank", "title": "", "summary": ""},
        action_history=[],
        failed_actions=set(),
        skill_context={"name": "generic_web"},
        past_experience="none",
    )
    assert step.action == "open_url"
    assert "fallback_due_to" in debug["fallback_reason"]
