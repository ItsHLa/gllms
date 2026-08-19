from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.schemas.scenario import RunRequest, RunResult
from backend.services.executor import run_python_code
from backend.scenarios.registry import registry

router = APIRouter(tags=["run"])


@router.post("/run/{scenario_id}", response_model=RunResult)
def run_scenario(scenario_id: str, request: RunRequest | None = None) -> RunResult:
    scenario = registry.get(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    code = request.code if request and request.code else scenario.code

    if request and request.code and not settings.allow_code_edit:
        raise HTTPException(
            status_code=403,
            detail="Editing scenario code is disabled on this server.",
        )

    return run_python_code(code, scenario.id)