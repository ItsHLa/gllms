from pydantic import BaseModel, Field


class ScenarioSummary(BaseModel):
    id: str
    title: str
    category: str
    owasp_primary: str = ""
    owasp_secondary: str = ""
    difficulty: str
    description: str
    tags: list[str] = Field(default_factory=list)


class ScenarioDetail(ScenarioSummary):
    article: str
    code: str
    expected_output: str
    attacker_prompt: str
    modes: list[str] = Field(default_factory=lambda: ["protected", "vulnerable"])
    system_prompts: dict[str, str] = Field(default_factory=dict)


class RunRequest(BaseModel):
    code: str | None = None
    mode: str | None = None


class RunResult(BaseModel):
    scenario_id: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    timed_out: bool = False
    error: str | None = None
