from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ActionType = Literal[
    "open_url",
    "search_text",
    "click_text",
    "extract_page_summary",
    "take_screenshot",
]


class TaskRunRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Natural language browser task")
    debug: bool = False
    current_page: dict[str, Any] | None = None


class PlannedStep(BaseModel):
    action: ActionType
    params: dict[str, Any] = Field(default_factory=dict)


class StepResult(BaseModel):
    step: int
    action: ActionType
    url: str
    success: bool
    screenshot: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class StepDebugTrace(BaseModel):
    step: int
    matched_skill: str
    current_url: str
    page_state_summary: str
    planner_input_summary: str
    planner_raw_output: str
    validated_action: str
    action_result: str
    failure_reason: str | None = None


class TaskDebugInfo(BaseModel):
    task_id: str
    matched_skill: str
    planner_reasoning_summary: str
    past_experience_used: str
    step_traces: list[StepDebugTrace] = Field(default_factory=list)


class TaskRunResponse(BaseModel):
    task: str
    blocked: bool
    steps: list[StepResult]
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    debug: TaskDebugInfo | None = None
