import re

from fastapi import APIRouter, HTTPException

from backend.config import settings
from backend.scenarios.registry import registry
from backend.schemas.scenario import RunRequest, RunResult
from backend.services.executor import run_python_code

router = APIRouter(tags=["run"])

_MODE_ASSIGN = re.compile(
    r'^(\s*)MODE\s*=\s*"[^"]*"\s*(?:#.*)?$', re.MULTILINE
)


def _apply_mode(code: str, mode: str) -> str:
    """Replace the MODE assignment in a scenario script with the chosen mode."""
    match = _MODE_ASSIGN.search(code)
    if not match:
        return code
    indent = match.group(1)
    return _MODE_ASSIGN.sub(f'{indent}MODE = "{mode}"', code, count=1)


@router.post("/run/{scenario_id}", response_model=RunResult)
def run_scenario(scenario_id: str, request: RunRequest | None = None) -> RunResult:
    scenario = registry.get(scenario_id)
    if scenario is None:
        raise HTTPException(
            status_code=404, detail=f"Scenario '{scenario_id}' not found"
        )

    code = request.code if request and request.code else scenario.code

    if request and request.mode:
        if request.mode not in scenario.modes:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid mode '{request.mode}'. "
                    f"Valid modes: {', '.join(scenario.modes)}."
                ),
            )
        code = _apply_mode(code, request.mode)

    if request and request.code and not settings.allow_code_edit:
        raise HTTPException(
            status_code=403,
            detail="Editing scenario code is disabled on this server.",
        )

    return run_python_code(code, scenario.id)