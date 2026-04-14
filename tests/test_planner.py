from __future__ import annotations

import pytest

from app.agent.planner import RuleBasedPlanner


@pytest.fixture()
def planner() -> RuleBasedPlanner:
    return RuleBasedPlanner()


def test_validate_next_step_accepts_known_action(planner: RuleBasedPlanner) -> None:
    step = planner._validate_next_step({"action": "open_url", "params": {"url": "https://example.com"}}, set())
    assert step.action == "open_url"


def test_validate_next_step_rejects_unknown_action(planner: RuleBasedPlanner) -> None:
    with pytest.raises(ValueError):
        planner._validate_next_step({"action": "do_bad", "params": {}}, set())


def test_fallback_when_llm_invalid(monkeypatch: pytest.MonkeyPatch, planner: RuleBasedPlanner) -> None:
    def raise_invalid(*args, **kwargs):
        raise ValueError("bad llm output")

    monkeypatch.setattr(planner, "llm_next_action", raise_invalid)
    step, debug = planner.next_action(
        task="find OpenAI",
        page_state={"url": "about:blank", "title": "", "summary": ""},
        action_history=[],
        failed_actions=set(),
        skill_context={"name": "generic_web"},
        past_experience="No relevant past experience.",
    )

    assert step.action == "open_url"
    assert debug["planner_raw_output"].startswith("fallback:")
