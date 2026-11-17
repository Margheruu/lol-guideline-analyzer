"""Load guideline config and evaluate enabled rules over a match."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Importing the rules package registers all bundled rule modules (their
# @register decorators run on import).
import src.rules  # noqa: F401  (import for side effects)
from src.rules import registry
from src.rules.base import MatchContext, RuleResult


def load_guidelines(path: str | Path) -> list[dict[str, Any]]:
    """Read the user's guideline definitions from YAML."""
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("rules", [])


def participant_id_for(match: dict[str, Any], puuid: str) -> int:
    """Map a PUUID to its 1-based participant id used in the timeline.

    Looks the player up in ``info.participants`` by puuid. Do NOT use the
    position in ``metadata.participants``: since ~2026-11-12 Riot returns
    that list in an order unrelated to ``participantId``, which silently
    picked another player in the same game.
    """
    participants = match["info"]["participants"]
    for p in participants:
        if p.get("puuid") == puuid:
            pid = int(p["participantId"])
            # Rules index info.participants[pid - 1]; fail loudly if that
            # ordering assumption ever breaks instead of evaluating someone else.
            if participants[pid - 1].get("puuid") != puuid:
                raise ValueError(f"info.participants is not in participantId order ({match['metadata']['matchId']})")
            return pid
    raise ValueError(f"puuid not found in match {match['metadata']['matchId']}")


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
