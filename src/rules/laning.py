"""Laning rules that compare the player to their same-role lane opponent."""
from __future__ import annotations

from typing import Any

from .base import Evidence, MatchContext, RuleResult
from .registry import register


def _me(ctx: MatchContext) -> dict[str, Any]:
    return ctx.match["info"]["participants"][ctx.participant_id - 1]


def _opponent(ctx: MatchContext, me: dict[str, Any]) -> dict[str, Any] | None:
    pos = me.get("teamPosition")
    if not pos:
        return None
    for p in ctx.match["info"]["participants"]:
        if p["teamId"] != me["teamId"] and p.get("teamPosition") == pos:
            return p
    return None


def _cs(pf: dict[str, Any]) -> int:
    return pf.get("minionsKilled", 0) + pf.get("jungleMinionsKilled", 0)


@register("not_behind_at_minute")
def not_behind_at_minute(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if not significantly behind the lane opponent (gold) at a minute."""
    minute = int(params.get("minute", 15))
    max_gold_deficit = int(params.get("max_gold_deficit", 500))

    me = _me(ctx)
    opp = _opponent(ctx, me)
    if opp is None:
        return RuleResult("not_behind_at_minute", True, 1.0,
                          "No same-role opponent found; not evaluated.", [])

    frames = ctx.timeline["info"]["frames"]
    frame = frames[min(minute, len(frames) - 1)]
    mpf = frame["participantFrames"][str(me["participantId"])]
    opf = frame["participantFrames"][str(opp["participantId"])]

    cs_d = _cs(mpf) - _cs(opf)
    gold_d = mpf.get("totalGold", 0) - opf.get("totalGold", 0)
    lvl_d = mpf.get("level", 0) - opf.get("level", 0)

    passed = gold_d >= -max_gold_deficit
    score = 1.0 if passed else max(0.0, 1.0 + gold_d / 2000.0)
    msg = (f"@{minute}:00 vs {opp.get('championName', 'opponent')}: "
           f"CS {cs_d:+d}, gold {gold_d:+d}, level {lvl_d:+d}.")
    return RuleResult("not_behind_at_minute", passed, score, msg,
                      [Evidence(detail=msg, timestamp_ms=minute * 60_000)])
