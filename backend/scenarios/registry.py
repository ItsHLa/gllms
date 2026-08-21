from dataclasses import dataclass
from pathlib import Path

from backend.config import CASES_DIR, ROOT_DIR
from backend.scenarios.metadata import SCENARIO_METADATA


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    category: str
    difficulty: str
    description: str
    tags: list[str]
    article: str
    code_path: Path
    expected_output: str
    attacker_prompt: str
    modes: list[str]

    @property
    def code(self) -> str:
        return self.code_path.read_text(encoding="utf-8")


class Registry:
    """Loads scenarios by joining metadata with the matching code file."""

    def __init__(self, cases_dir: Path = CASES_DIR, metadata: dict = SCENARIO_METADATA):
        self._cases_dir = cases_dir
        self._metadata = metadata
        self._by_id: dict[str, Scenario] = {}
        self._load()

    def _resolve_article(self, scenario_id: str, meta: dict) -> str:
        article_file = meta.get("article_file")
        if article_file:
            return (ROOT_DIR / article_file).read_text(encoding="utf-8")
        return meta.get("article", "")

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
                difficulty=meta["difficulty"],
                description=meta["description"],
                tags=meta.get("tags", []),
                article=self._resolve_article(scenario_id, meta),
                code_path=code_path,
                expected_output=meta.get("expected_output", ""),
                attacker_prompt=meta.get("attacker_prompt", ""),
                modes=meta.get("modes", ["protected", "vulnerable"]),
            )

    def list(self) -> list[Scenario]:
        return list(self._by_id.values())

    def get(self, scenario_id: str) -> Scenario | None:
        return self._by_id.get(scenario_id)


registry = Registry()