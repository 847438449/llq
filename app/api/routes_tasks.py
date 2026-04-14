from __future__ import annotations

from fastapi import APIRouter

from app.agent.executor import TaskExecutor
from app.agent.planner import RuleBasedPlanner
from app.schemas.task import TaskRunRequest, TaskRunResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
planner = RuleBasedPlanner()
executor = TaskExecutor()


@router.post("/run", response_model=TaskRunResponse)
async def run_task(payload: TaskRunRequest) -> TaskRunResponse:
    if planner.is_blocked(payload.task):
        return TaskRunResponse(task=payload.task, blocked=True, steps=[], extracted_data={})

    return await executor.run(
        payload.task,
        planner,
        debug=payload.debug,
        initial_page_context=payload.current_page,
    )
