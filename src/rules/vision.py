"""Vision-related guideline rules."""
from __future__ import annotations

from typing import Any

from .base import Evidence, MatchContext, RuleResult
from .registry import register


@register("wards_per_interval")
def wards_per_interval(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if wards placed keep pace across fixed-length intervals, up to a
    cutoff minute (e.g. through the laning phase)."""
    interval = int(params.get("interval_minutes", 3))
    target = float(params.get("min_wards_per_interval", 1))
    through_minute = int(params.get("through_minute", 15))
    through_ms = through_minute * 60_000

    count = 0
    for frame in ctx.timeline["info"]["frames"]:
        for ev in frame.get("events", []):
            if (ev.get("type") == "WARD_PLACED"
                    and ev.get("creatorId") == ctx.participant_id
                    and ev.get("timestamp", 0) <= through_ms):
                count += 1

    intervals = max(1, through_minute // interval)
    rate = count / intervals
    passed = rate >= target
    score = min(rate / target, 1.0) if target else 1.0
    msg = (f"{through_minute}分までに{interval}分間隔で平均 {rate:.1f}本/区間 "
           f"（目標 {target:g}本/区間、合計 {count}本）。")
    return RuleResult("wards_per_interval", passed, score, msg,
                      [Evidence(detail=msg, timestamp_ms=through_ms)])


@register("control_ward_rate")
def control_ward_rate(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if control wards placed per 10 game-minutes meets a target.

    Uses Riot's ``challenges.controlWardsPlaced`` (whole game). Placement
    location is not available from the API, so this checks volume only.
    """
    target = float(params.get("min_per_10min", 1.0))

    info = ctx.match.get("info", {})
    me = info.get("participants", [])[ctx.participant_id - 1]
    placed = me.get("challenges", {}).get("controlWardsPlaced")
    minutes = info.get("gameDuration", 0) / 60
    if placed is None or minutes <= 0:
        return RuleResult("control_ward_rate", True, 1.0,
                          "コントロールワードのデータが無く評価対象外。", [])

    rate = 10 * placed / minutes
    passed = rate >= target
    score = min(rate / target, 1.0) if target else 1.0
    msg = (f"コントロールワード {placed} 個（10分あたり {rate:.1f} 個、"
           f"目標 {target:g} 個）。")
    return RuleResult("control_ward_rate", passed, score, msg,
                      [Evidence(detail=msg)])
