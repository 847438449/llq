from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from urllib.parse import quote_plus

from app.schemas.task import PlannedStep

MAX_STEPS = 8
ALLOWED_ACTIONS = {
    "open_url",
    "search_text",
    "click_text",
    "extract_page_summary",
    "take_screenshot",
}
BLOCKED_KEYWORDS = ["login", "sign in", "payment", "checkout", "submit form", "purchase"]
logger = logging.getLogger(__name__)


class RuleBasedPlanner:
    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.model = model
        self.prompt_template = self._load_prompt_template()

    def is_blocked(self, task: str) -> bool:
        lowered = task.lower()
        return any(keyword in lowered for keyword in BLOCKED_KEYWORDS)

    def next_action(
        self,
        task: str,
        page_state: dict,
        action_history: list[dict],
        failed_actions: set[str],
        skill_context: dict,
        past_experience: str,
    ) -> tuple[PlannedStep, dict]:
        if self.is_blocked(task):
            raise ValueError("Blocked task")

        try:
            step, debug = self.llm_next_action(
                task=task,
                page_state=page_state,
                action_history=action_history,
                failed_actions=failed_actions,
                skill_context=skill_context,
                past_experience=past_experience,
            )
            return step, debug
        except Exception as exc:
            fallback_reason = f"fallback_due_to: {type(exc).__name__}: {exc}"
            logger.warning("planner fallback: %s", fallback_reason)
            step = self.naive_next_action(task, page_state, action_history)
            debug = {
                "planner_input_summary": self._input_summary(task, page_state, skill_context),
                "planner_raw_output": "",
                "validated_action": step.model_dump_json(),
                "planner_reasoning_summary": "Used deterministic fallback.",
                "past_experience_used": past_experience,
                "validation_failure_reason": str(exc),
                "fallback_reason": fallback_reason,
            }
            return step, debug

    def llm_next_action(
        self,
        task: str,
        page_state: dict,
        action_history: list[dict],
        failed_actions: set[str],
        skill_context: dict,
        past_experience: str,
    ) -> tuple[PlannedStep, dict]:
        payload = {
            "user_task": task.strip(),
            "current_page_state": page_state,
            "previous_actions": action_history[-6:],
            "failed_actions": sorted(failed_actions),
            "matched_skill": skill_context,
            "relevant_past_experience": past_experience,
            "max_steps": MAX_STEPS,
        }

        from openai import OpenAI

        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            temperature=0,
            input=[
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": "User task and context for next action planning:\n" + json.dumps(payload, ensure_ascii=False)},
            ],
        )
        raw_text = getattr(response, "output_text", "") or ""
        logger.info("planner raw output: %s", raw_text)
        raw_obj = json.loads(raw_text)
        step = self._validate_next_step(raw_obj, failed_actions)
        debug = {
            "planner_input_summary": self._input_summary(task, page_state, skill_context),
            "planner_raw_output": raw_text[:500],
            "validated_action": step.model_dump_json(),
            "planner_reasoning_summary": "Used LLM next-action planning.",
            "past_experience_used": past_experience,
            "validation_failure_reason": "",
            "fallback_reason": "",
        }
        return step, debug

    def naive_next_action(self, task: str, page_state: dict, action_history: list[dict]) -> PlannedStep:
        if not page_state.get("url") or page_state.get("url") == "about:blank":
            target_url = self._extract_url(task)
            if target_url:
                return PlannedStep(action="open_url", params={"url": target_url})
            return PlannedStep(action="open_url", params={"url": f"https://duckduckgo.com/?q={quote_plus(task)}"})

        if len(action_history) >= 1 and action_history[-1].get("action") != "extract_page_summary":
            return PlannedStep(action="extract_page_summary", params={})

        return PlannedStep(action="take_screenshot", params={"name": "final"})

    def _validate_next_step(self, raw_step: object, failed_actions: set[str]) -> PlannedStep:
        if not isinstance(raw_step, dict):
            raise ValueError("Planner output must be an object with action/params")

        action = raw_step.get("action")
        params = raw_step.get("params", {})
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"Unknown action: {action}")
        if not isinstance(params, dict):
            raise ValueError("Step params must be an object")

        step = PlannedStep(action=action, params=params)
        step_key = self._step_key(step)
        if step_key in failed_actions:
            raise ValueError(f"Repeated failed action: {step_key}")
        return step

    def _step_key(self, step: PlannedStep) -> str:
        return f"{step.action}:{json.dumps(step.params, sort_keys=True)}"

    def _extract_url(self, text: str) -> str | None:
        match = re.search(r"https?://[^\s]+", text)
        return match.group(0) if match else None

    def _input_summary(self, task: str, page_state: dict, skill_context: dict) -> str:
        return f"task={task[:80]} | url={page_state.get('url','about:blank')} | title={page_state.get('title','')[:60]} | skill={skill_context.get('name','generic_web')}"

    def _load_prompt_template(self) -> str:
        return (Path(__file__).resolve().parents[1] / "prompts" / "planner.txt").read_text(encoding="utf-8")
