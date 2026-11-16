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


def _deaths_until(ctx: MatchContext, cutoff_ms: int) -> list[Evidence]:
    """Evidence for each of the player's deaths at or before ``cutoff_ms``."""
    return [
        Evidence(detail="death", timestamp_ms=ev.get("timestamp"),
                 position=ev.get("position"))
        for ev in _iter_events(ctx)
        if ev.get("type") == "CHAMPION_KILL"
        and ev.get("victimId") == ctx.participant_id
        and ev.get("timestamp", 0) <= cutoff_ms
    ]


@register("deaths_before_minute")
def deaths_before_minute(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if the player dies no more than ``max_deaths`` before a minute mark."""
    before_ms = int(params["before_minute"]) * 60_000
    max_deaths = int(params.get("max_deaths", 0))

    evidence = _deaths_until(ctx, before_ms)
    deaths = len(evidence)
    passed = deaths <= max_deaths
    return RuleResult(
        rule_id="deaths_before_minute",
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"{params['before_minute']}分までに {deaths} 回デス（上限 {max_deaths}）。",
        evidence=evidence,
    )


@register("deaths_in_lane_phase")
def deaths_in_lane_phase(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if the player dies no more than ``max_deaths`` during the laning
    phase (0:00 to ``through_minute``, default 14:00 — roughly when the
    first outer turret falls). Two lane-phase deaths is the guide's
    definition of a lost lane.
    """
    through_minute = int(params.get("through_minute", 14))
    max_deaths = int(params.get("max_deaths", 1))

    evidence = _deaths_until(ctx, through_minute * 60_000)
    deaths = len(evidence)
    passed = deaths <= max_deaths
    msg = f"レーン戦（0〜{through_minute}分）で {deaths} 回デス（上限 {max_deaths}）。"
    if not passed:
        msg += " 上限超過はレーン負けの目安 — 以降は無理に戦わずタワー下でファーム。"
    return RuleResult("deaths_in_lane_phase", passed, 1.0 if passed else 0.0,
                      msg, evidence)
