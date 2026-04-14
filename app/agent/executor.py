from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from app.agent.planner import MAX_STEPS, RuleBasedPlanner
from app.browser.manager import BrowserManager
from app.browser.tools import click_text, extract_page_context, extract_page_summary, open_url, search_text, take_screenshot
from app.memory.store import MemoryStore
from app.schemas.task import PlannedStep, StepDebugTrace, StepResult, TaskDebugInfo, TaskRunResponse
from app.skills.registry import SkillRegistry

BLOCKED_KEYWORDS = ["login", "sign in", "payment", "checkout", "submit form", "purchase"]
logger = logging.getLogger(__name__)


class TaskExecutor:
    def __init__(self) -> None:
        self.skill_registry = SkillRegistry()
        self.memory = MemoryStore()

    async def run(self, task: str, planner: RuleBasedPlanner, debug: bool = False, initial_page_context: dict | None = None) -> TaskRunResponse:
        if self._is_blocked(task):
            return TaskRunResponse(task=task, blocked=True, steps=[], extracted_data={})

        task_id = str(uuid4())
        manager = BrowserManager()
        results: list[StepResult] = []
        extracted_data: dict = {}
        history: list[dict] = []
        failed_actions: set[str] = set()
        failure_counts: dict[str, int] = defaultdict(int)
        visited_urls: list[str] = []
        matched_skill_name = "generic_web"
        debug_traces: list[StepDebugTrace] = []
        planner_reasoning_summary = ""
        past_experience_used = ""
        stop_reason: str | None = None

        planner_repeat_count = 0
        action_repeat_count = 0
        last_planner_raw = None
        last_page_signature = None
        last_action_signature = None

        try:
            page = await manager.start()
            for idx in range(1, MAX_STEPS + 1):
                page_state = self._sanitize_initial_page_context(initial_page_context) if idx == 1 and initial_page_context else await extract_page_context(page)
                current_url = page_state.get("url") or page.url or "about:blank"
                visited_urls.append(current_url)

                skill = self.skill_registry.match(current_url)
                matched_skill_name = skill.name
                enriched_state = skill.enrich_page_state(page_state)

                domain = self.memory.domain_from_url(current_url)
                past_experience = self.memory.summarize_patterns(domain=domain)
                skill_context = {"name": skill.name, "hints": skill.hints, "preferred_selectors": skill.preferred_selectors}

                step, planner_debug = planner.next_action(
                    task=task,
                    page_state=enriched_state,
                    action_history=history,
                    failed_actions=failed_actions,
                    skill_context=skill_context,
                    past_experience=past_experience,
                )

                planner_reasoning_summary = planner_debug.get("planner_reasoning_summary", "")
                past_experience_used = planner_debug.get("past_experience_used", past_experience)

                planner_raw = planner_debug.get("planner_raw_output", "")
                page_signature = f"{enriched_state.get('url','')}|{enriched_state.get('title','')}|{enriched_state.get('summary','')[:80]}"
                if planner_raw and planner_raw == last_planner_raw and page_signature == last_page_signature:
                    planner_repeat_count += 1
                else:
                    planner_repeat_count = 1
                last_planner_raw = planner_raw
                last_page_signature = page_signature
                if planner_repeat_count >= 3:
                    stop_reason = "repeated_planner_output_no_progress"
                    break

                result = StepResult(step=idx, action=step.action, url=page.url or "about:blank", success=False)
                step_key = self._step_key(step)
                action_result_summary = ""
                failure_reason = None

                try:
                    data = await self._execute_action(page, step, manager, idx)
                    result.data = data
                    result.success = True
                    result.url = page.url or result.url
                    action_result_summary = json.dumps(data)[:300]
                    if step.action == "extract_page_summary":
                        extracted_data.update(data)
                except Exception as exc:
                    result.error = str(exc)
                    failure_reason = str(exc)
                    action_result_summary = "failed"
                    failure_counts[step_key] += 1
                    failed_actions.add(step_key)
                    if failure_counts[step_key] >= 2:
                        stop_reason = "same_action_failed_twice"
                finally:
                    screenshot_path = manager.screenshots_dir / f"step_{idx}_{step.action}.png"
                    await self._safe_take_screenshot(page, screenshot_path, result)

                action_signature = f"{step.action}|{json.dumps(step.params, sort_keys=True)}|{action_result_summary}"
                if action_signature == last_action_signature:
                    action_repeat_count += 1
                else:
                    action_repeat_count = 1
                last_action_signature = action_signature
                if action_repeat_count >= 3:
                    stop_reason = "repeated_validated_action_no_progress"

                results.append(result)
                history.append(self._history_entry(step, result))

                if debug:
                    debug_traces.append(
                        self._build_trace(
                            step=idx,
                            matched_skill=matched_skill_name,
                            current_url=current_url,
                            page_state=enriched_state,
                            planner_debug=planner_debug,
                            validated_action=step,
                            action_result=action_result_summary,
                            failure_reason=failure_reason,
                            stop_reason=stop_reason,
                        )
                    )

                if stop_reason or step.action == "take_screenshot":
                    break
        finally:
            await manager.close()

        self.memory.save_task_record(
            {
                "task_id": task_id,
                "user_input": task,
                "domain": self.memory.domain_from_url(visited_urls[-1] if visited_urls else ""),
                "visited_urls": visited_urls,
                "successful_actions": [h for h in history if h.get("success")],
                "failed_actions": [h for h in history if not h.get("success")],
                "matched_skill": matched_skill_name,
                "final_extracted_summary": extracted_data.get("summary", ""),
            }
        )
        self._save_debug_trace(task_id, debug_traces)

        debug_info = TaskDebugInfo(
            task_id=task_id,
            matched_skill=matched_skill_name,
            planner_reasoning_summary=planner_reasoning_summary,
            past_experience_used=past_experience_used,
            step_traces=debug_traces,
        ) if debug else None

        return TaskRunResponse(task=task, blocked=False, steps=results, extracted_data=extracted_data, debug=debug_info, stop_reason=stop_reason)

    async def _safe_take_screenshot(self, page, screenshot_path: Path, result: StepResult) -> None:
        try:
            await take_screenshot(page, screenshot_path)
            result.screenshot = str(screenshot_path)
        except Exception as screenshot_exc:
            msg = f"screenshot_failed: {screenshot_exc}"
            result.error = f"{result.error}; {msg}" if result.error else msg

    async def _execute_action(self, page, step: PlannedStep, manager: BrowserManager, idx: int) -> dict:
        if step.action == "open_url":
            return await open_url(page, step.params["url"])
        if step.action == "search_text":
            return await search_text(page, step.params["text"])
        if step.action == "click_text":
            return await click_text(page, step.params["text"])
        if step.action == "extract_page_summary":
            return await extract_page_summary(page)
        if step.action == "take_screenshot":
            name = step.params.get("name", f"manual_{idx}")
            return await take_screenshot(page, manager.screenshots_dir / f"{name}.png")
        raise ValueError(f"Unsupported action: {step.action}")

    def _history_entry(self, step: PlannedStep, result: StepResult) -> dict:
        return {"action": step.action, "params": step.params, "success": result.success, "error": result.error}

    def _step_key(self, step: PlannedStep) -> str:
        return f"{step.action}:{json.dumps(step.params, sort_keys=True)}"

    def _is_blocked(self, task: str) -> bool:
        lowered = task.lower()
        return any(k in lowered for k in BLOCKED_KEYWORDS)

    def _sanitize_initial_page_context(self, page_context: dict | None) -> dict:
        page_context = page_context or {}
        return {
            "url": str(page_context.get("url", "about:blank")),
            "title": str(page_context.get("title", ""))[:200],
            "buttons": list(page_context.get("buttons", []))[:10],
            "links": list(page_context.get("links", []))[:10],
            "inputs": list(page_context.get("inputs", []))[:10],
            "summary": str(page_context.get("summary", ""))[:1000],
            "warning": page_context.get("warning"),
        }

    def _build_trace(self, step: int, matched_skill: str, current_url: str, page_state: dict, planner_debug: dict, validated_action: PlannedStep, action_result: str, failure_reason: str | None, stop_reason: str | None) -> StepDebugTrace:
        return StepDebugTrace(
            step=step,
            matched_skill=matched_skill,
            current_url=current_url,
            page_state_summary=page_state.get("summary", "")[:200],
            planner_input_summary=planner_debug.get("planner_input_summary", ""),
            planner_raw_output=planner_debug.get("planner_raw_output", ""),
            validated_action=validated_action.model_dump_json(),
            action_result=action_result,
            failure_reason=failure_reason,
            stop_reason=stop_reason,
        )

    def _save_debug_trace(self, task_id: str, traces: list[StepDebugTrace]) -> None:
        logs_dir = Path("artifacts/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / f"{task_id}.json").write_text(json.dumps([t.model_dump() for t in traces], indent=2), encoding="utf-8")
