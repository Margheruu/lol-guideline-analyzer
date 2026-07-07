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


@register("cs_per_minute")
def cs_per_minute(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if CS-per-minute at a given minute meets the target (e.g. 7.5)."""
    minute = int(params.get("minute", 15))
    target = float(params.get("min_cs_per_min", 7.5))

    me = _me(ctx)
    frames = ctx.timeline["info"]["frames"]
    frame = frames[min(minute, len(frames) - 1)]
    cs = _cs(frame["participantFrames"][str(me["participantId"])])
    cspm = cs / minute if minute else 0.0

    passed = cspm >= target
    score = min(cspm / target, 1.0) if target else 1.0
    return RuleResult(
        "cs_per_minute", passed, score,
        f"{minute}分で {cs} CS（{cspm:.1f}/分、目標 {target:g}/分）。",
        [Evidence(detail=f"CS={cs} ({cspm:.1f}/min)", timestamp_ms=minute * 60_000)],
    )


@register("not_behind_at_minute")
def not_behind_at_minute(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if not significantly behind the lane opponent at a minute.

    Gold is always checked. CS/level deficits are additionally checked when
    ``max_cs_deficit`` / ``max_level_deficit`` are set (both default to
    ``None`` = not evaluated, so existing gold-only configs are unaffected).
    """
    minute = int(params.get("minute", 15))
    max_gold_deficit = int(params.get("max_gold_deficit", 500))
    max_cs_deficit = params.get("max_cs_deficit")
    max_level_deficit = params.get("max_level_deficit")

    me = _me(ctx)
    opp = _opponent(ctx, me)
    if opp is None:
        return RuleResult("not_behind_at_minute", True, 1.0,
                          "同ロールの相手が見つからず評価対象外。", [])

    frames = ctx.timeline["info"]["frames"]
    frame = frames[min(minute, len(frames) - 1)]
    mpf = frame["participantFrames"][str(me["participantId"])]
    opf = frame["participantFrames"][str(opp["participantId"])]

    cs_d = _cs(mpf) - _cs(opf)
    gold_d = mpf.get("totalGold", 0) - opf.get("totalGold", 0)
    lvl_d = mpf.get("level", 0) - opf.get("level", 0)

    gold_ok = gold_d >= -max_gold_deficit
    cs_ok = max_cs_deficit is None or cs_d >= -int(max_cs_deficit)
    lvl_ok = max_level_deficit is None or lvl_d >= -int(max_level_deficit)
    passed = gold_ok and cs_ok and lvl_ok

    score = 1.0 if passed else max(0.0, 1.0 + gold_d / 2000.0)
    reasons = [name for ok, name in
               ((gold_ok, "ゴールド"), (cs_ok, "CS"), (lvl_ok, "レベル")) if not ok]
    msg = (f"{minute}分 vs {opp.get('championName', '相手')}: "
           f"CS {cs_d:+d} / ゴールド {gold_d:+d} / レベル {lvl_d:+d}。")
    if reasons:
        msg += f" 不合格要因: {'・'.join(reasons)}。"
    return RuleResult("not_behind_at_minute", passed, score, msg,
                      [Evidence(detail=msg, timestamp_ms=minute * 60_000)])
