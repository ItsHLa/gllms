import importlib
from dataclasses import dataclass, replace
from pathlib import Path

from backend.config import CASES_DIR, ROOT_DIR
from backend.scenarios.i18n import CATEGORY_AR, DIFFICULTY_AR, SCENARIO_AR
from backend.scenarios.metadata import SCENARIO_METADATA


def _load_system_prompts(scenario_id: str) -> dict[str, str]:
    """Import the case package's prompts module and read its SYSTEM_PROMPTS."""
    module_name = f"backend.scenarios.cases.{scenario_id.replace('-', '_')}.prompts"
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return {}
    prompts = getattr(module, "SYSTEM_PROMPTS", {})
    return dict(prompts)


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    category: str
    owasp_primary: str
    owasp_secondary: str
    difficulty: str
    description: str
    tags: list[str]
    article: str
    code_path: Path
    expected_output: str
    attacker_prompt: str
    modes: list[str]
    system_prompts: dict[str, str]

    @property
    def code(self) -> str:
        return self.code_path.read_text(encoding="utf-8")


def _resolve_article_file(meta: dict, lang: str) -> Path | None:
    article_file = meta.get("article_file")
    if not article_file:
        return None
    base = ROOT_DIR / article_file
    if lang == "ar":
        localized = base.with_name(f"{base.stem}.ar{base.suffix}")
        if localized.exists():
            return localized
    return base


class Registry:
    """Loads scenarios by joining metadata with the matching code file."""

    SUPPORTED_LANGS = ("en", "ar")

    def __init__(self, cases_dir: Path = CASES_DIR, metadata: dict = SCENARIO_METADATA):
        self._cases_dir = cases_dir
        self._metadata = metadata
        self._by_id: dict[str, Scenario] = {}
        self._load()

    def _load(self) -> None:
        for scenario_id, meta in self._metadata.items():
            code_path = self._cases_dir / f"{scenario_id}.py"
            if not code_path.exists():
                raise FileNotFoundError(
                    f"Scenario '{scenario_id}' is missing its code file: {code_path}"
                )
            self._by_id[scenario_id] = Scenario(
                id=scenario_id,
                title=meta["title"],
                category=meta["category"],
                owasp_primary=meta.get("owasp_primary", ""),
                owasp_secondary=meta.get("owasp_secondary", ""),
                difficulty=meta["difficulty"],
                description=meta["description"],
                tags=meta.get("tags", []),
                article=self._read_article(meta, lang="en"),
                code_path=code_path,
                expected_output=meta.get("expected_output", ""),
                attacker_prompt=meta.get("attacker_prompt", ""),
                modes=meta.get("modes", ["protected", "vulnerable"]),
                system_prompts=_load_system_prompts(scenario_id),
            )

    def _read_article(self, meta: dict, lang: str) -> str:
        article_path = _resolve_article_file(meta, lang)
        if article_path is None:
            return meta.get("article", "")
        return article_path.read_text(encoding="utf-8")

    def _localized(self, scenario: Scenario, lang: str) -> Scenario:
        if lang not in self.SUPPORTED_LANGS or lang == "en":
            return scenario
        overrides = SCENARIO_AR.get(scenario.id)
        if not overrides:
            return scenario
        meta = self._metadata[scenario.id]
        return replace(
            scenario,
            title=overrides.get("title", scenario.title),
            category=CATEGORY_AR.get(scenario.category, scenario.category),
            owasp_primary=scenario.owasp_primary,
            owasp_secondary=scenario.owasp_secondary,
            difficulty=DIFFICULTY_AR.get(scenario.difficulty, scenario.difficulty),
            description=overrides.get("description", scenario.description),
            tags=scenario.tags,
            article=self._read_article(meta, lang),
            expected_output=overrides.get("expected_output", scenario.expected_output),
            attacker_prompt=overrides.get("attacker_prompt", scenario.attacker_prompt),
            modes=scenario.modes,
        )

    def list(self, lang: str = "en") -> list[Scenario]:
        return [self._localized(s, lang) for s in self._by_id.values()]

    def get(self, scenario_id: str, lang: str = "en") -> Scenario | None:
        scenario = self._by_id.get(scenario_id)
        if scenario is None:
            return None
        return self._localized(scenario, lang)


registry = Registry()
