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
        message=(
            f"{deaths} death(s) before {params['before_minute']}:00 "
            f"(limit {max_deaths})."
        ),
        evidence=evidence,
    )


@register("cs_at_10")
def cs_at_10(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if total CS at a given minute frame meets the threshold."""
    minute = int(params.get("minute", 10))
    min_cs = int(params["min_cs"])

    frames = ctx.timeline["info"]["frames"]
    frame = frames[min(minute, len(frames) - 1)]
    pf = frame["participantFrames"][str(ctx.participant_id)]
    cs = pf.get("minionsKilled", 0) + pf.get("jungleMinionsKilled", 0)

    passed = cs >= min_cs
    return RuleResult(
        rule_id="cs_at_10",
        passed=passed,
        score=min(cs / min_cs, 1.0) if min_cs else 1.0,
        message=f"{cs} CS at {minute}:00 (target {min_cs}).",
        evidence=[Evidence(detail=f"cs={cs}", timestamp_ms=minute * 60_000)],
    )
