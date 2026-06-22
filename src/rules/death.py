"""Death-based guideline rules, built on src.analysis.deaths."""
from __future__ import annotations

from typing import Any

from src.analysis.deaths import deaths_for

from .base import Evidence, MatchContext, RuleResult
from .registry import register


@register("isolated_deaths")
def isolated_deaths(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Flag deaths with no teammate nearby ("don't walk first / when alone")."""
    max_allowed = int(params.get("max_deaths", 0))
    radius = int(params.get("nearby_radius", 2000))
    deaths = deaths_for(ctx, nearby_radius=radius)
    isolated = [d for d in deaths if d.allies_nearby == 0]
    passed = len(isolated) <= max_allowed
    evidence = [
        Evidence(detail=f"周囲{radius}内に味方なしでデス（加害者 {d.killer_champion}）",
                 timestamp_ms=d.timestamp_ms, position=d.position)
        for d in isolated
    ]
    return RuleResult(
        "isolated_deaths", passed, 1.0 if passed else 0.0,
        f"{len(deaths)} 回中 {len(isolated)} 回、周囲に味方なしでデス"
        f"（上限 {max_allowed}）。",
        evidence,
    )


@register("low_hp_deaths")
def low_hp_deaths(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Flag deaths where you were already low HP (lingered instead of backing)."""
    pct = float(params.get("health_pct", 0.35))
    max_allowed = int(params.get("max_deaths", 1))
    deaths = deaths_for(ctx)
    low = [d for d in deaths
           if d.health_pct_before is not None and d.health_pct_before <= pct]
    passed = len(low) <= max_allowed
    evidence = [
        Evidence(detail=f"デス直前 HP ~{d.health_pct_before:.0%}",
                 timestamp_ms=d.timestamp_ms, position=d.position)
        for d in low
    ]
    return RuleResult(
        "low_hp_deaths", passed, 1.0 if passed else 0.0,
        f"{len(deaths)} 回中 {len(low)} 回、HP {pct:.0%} 以下からのデス"
        f"（上限 {max_allowed}）。",
        evidence,
    )
