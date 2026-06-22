"""Load guideline config and evaluate enabled rules over a match."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Importing examples registers the bundled rules. Add your own rule modules
# here (or use a plugin-style import) so their @register decorators run.
from src.rules import examples  # noqa: F401  (import for side effects)
from src.rules import registry
from src.rules.base import MatchContext, RuleResult


def load_guidelines(path: str | Path) -> list[dict[str, Any]]:
    """Read the user's guideline definitions from YAML."""
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("rules", [])


def participant_id_for(match: dict[str, Any], puuid: str) -> int:
    """Map a PUUID to its 1-based participant id used in the timeline."""
    order = match["metadata"]["participants"]
    return order.index(puuid) + 1


def evaluate(
    ctx: MatchContext, guidelines: list[dict[str, Any]]
) -> list[RuleResult]:
    """Run each enabled guideline's rule and collect the verdicts."""
    results: list[RuleResult] = []
    for g in guidelines:
        if not g.get("enabled", True):
            continue
        rule = registry.get(g["id"])
        results.append(rule(ctx, g.get("params", {})))
    return results
