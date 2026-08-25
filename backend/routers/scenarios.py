from fastapi import APIRouter, HTTPException, Query

from backend.scenarios.registry import registry
from backend.schemas.scenario import ScenarioDetail, ScenarioSummary

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioSummary])
def list_scenarios(lang: str = Query("en")) -> list[ScenarioSummary]:
    return [
        ScenarioSummary(
            id=s.id,
            title=s.title,
            category=s.category,
            difficulty=s.difficulty,
            description=s.description,
            tags=s.tags,
        )
        for s in registry.list(lang)
    ]


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str, lang: str = Query("en")) -> ScenarioDetail:
    scenario = registry.get(scenario_id, lang)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return ScenarioDetail(
        id=scenario.id,
        title=scenario.title,
        category=scenario.category,
        difficulty=scenario.difficulty,
        description=scenario.description,
        tags=scenario.tags,
        article=scenario.article,
        code=scenario.code,
        expected_output=scenario.expected_output,
        attacker_prompt=scenario.attacker_prompt,
        modes=scenario.modes,
        system_prompts=scenario.system_prompts,
    )
