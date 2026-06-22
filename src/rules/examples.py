"""Example rule implementations.

These demonstrate the pattern: read from the normalized timeline, compare
against user params, return a verdict with evidence. Importing this module
registers the rules. Add real rules here (or split into more modules) and keep
each one pure and unit-tested.
"""
from __future__ import annotations

from typing import Any

from .base import Evidence, MatchContext, RuleResult
from .registry import register


def _iter_events(ctx: MatchContext):
    """Yield every timeline event across all frames."""
    for frame in ctx.timeline["info"]["frames"]:
        yield from frame.get("events", [])


@register("deaths_before_minute")
def deaths_before_minute(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if the player dies no more than ``max_deaths`` before a minute mark."""
    before_ms = int(params["before_minute"]) * 60_000
    max_deaths = int(params.get("max_deaths", 0))

    evidence: list[Evidence] = []
    for ev in _iter_events(ctx):
        if (
            ev.get("type") == "CHAMPION_KILL"
            and ev.get("victimId") == ctx.participant_id
            and ev.get("timestamp", 0) <= before_ms
        ):
            evidence.append(
                Evidence(
                    detail="death",
                    timestamp_ms=ev.get("timestamp"),
                    position=ev.get("position"),
                )
            )

    deaths = len(evidence)
    passed = deaths <= max_deaths
    return RuleResult(
        rule_id="deaths_before_minute",
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"{params['before_minute']}分までに {deaths} 回デス（上限 {max_deaths}）。",
        evidence=evidence,
    )
