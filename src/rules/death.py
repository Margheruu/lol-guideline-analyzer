"""Death-based guideline rules, built on src.analysis.deaths."""
from __future__ import annotations

from collections import Counter
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


@register("frontmost_deaths")
def frontmost_deaths(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Flag deaths where you were the most-forward teammate (engaged first).

    Caveat: only evaluated when at least one ally was within ``nearby_radius``
    — a fully isolated death (see ``isolated_deaths``) can't be classified as
    "frontmost of the group" since there is no group to compare against.
    """
    max_allowed = int(params.get("max_deaths", 1))
    radius = int(params.get("nearby_radius", 2000))
    deaths = deaths_for(ctx, nearby_radius=radius)
    front = [d for d in deaths if d.is_frontmost]
    passed = len(front) <= max_allowed
    evidence = [
        Evidence(detail=f"味方の中で最前線でデス（加害者 {d.killer_champion}）",
                 timestamp_ms=d.timestamp_ms, position=d.position)
        for d in front
    ]
    return RuleResult(
        "frontmost_deaths", passed, 1.0 if passed else 0.0,
        f"{len(deaths)} 回中 {len(front)} 回、味方より前に出てデス"
        f"（上限 {max_allowed}）。",
        evidence,
    )


@register("death_cause_summary")
def death_cause_summary(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Informational: breakdown of deaths by killer champion and top damage
    source, to help "analyze your deaths" (the PDF's most-repeated theme).
    Always passes — there's no pass/fail target, only a summary to review.
    """
    deaths = deaths_for(ctx)
    if not deaths:
        return RuleResult("death_cause_summary", True, 1.0, "デスなし。", [])

    killer_counts = Counter(d.killer_champion for d in deaths if d.killer_champion)
    source_counts = Counter(d.top_damage_source for d in deaths if d.top_damage_source)
    top_killers = ", ".join(f"{k}×{v}" for k, v in killer_counts.most_common(3)) or "不明"
    top_sources = ", ".join(f"{k}×{v}" for k, v in source_counts.most_common(3)) or "不明"

    msg = (f"{len(deaths)} 回デス。加害者内訳: {top_killers}。"
           f"主なダメージ源: {top_sources}。")
    evidence = [
        Evidence(
            detail=f"加害者={d.killer_champion or '不明'} / "
                   f"ダメージ源={d.top_damage_source or '不明'}",
            timestamp_ms=d.timestamp_ms, position=d.position,
        )
        for d in deaths
    ]
    return RuleResult("death_cause_summary", True, 1.0, msg, evidence)
