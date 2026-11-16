"""Jungle-specific guideline rules."""
from __future__ import annotations

from typing import Any

from .base import Evidence, MatchContext, RuleResult
from .registry import register


def _purchase_times(ctx: MatchContext) -> list[int]:
    return sorted(
        ev["timestamp"]
        for frame in ctx.timeline["info"]["frames"]
        for ev in frame.get("events", [])
        if ev.get("type") == "ITEM_PURCHASED"
        and ev.get("participantId") == ctx.participant_id
    )


def _first_back(ctx: MatchContext, grace_ms: int, cluster_ms: int) -> tuple[int, int] | None:
    """(first, last) purchase timestamps of the first shopping trip after the
    starting buy. Purchases within ``cluster_ms`` of the first one count as
    the same trip."""
    later = [t for t in _purchase_times(ctx) if t > grace_ms]
    if not later:
        return None
    trip = [t for t in later if t - later[0] <= cluster_ms]
    return trip[0], trip[-1]


def _gold_spent(frames: list[dict[str, Any]], pid: int, first: int, last: int) -> int:
    """Estimate gold spent on a shopping trip from the frames around it.

    spent ≈ gold held before + gold earned in between − gold held after.
    Exact when nothing is sold; resolution is limited by the 60s frames.
    """
    b = min(first // 60_000, len(frames) - 1)
    a = min(last // 60_000 + 1, len(frames) - 1)
    before = frames[b]["participantFrames"][str(pid)]
    after = frames[a]["participantFrames"][str(pid)]
    earned = after.get("totalGold", 0) - before.get("totalGold", 0)
    return before.get("currentGold", 0) + earned - after.get("currentGold", 0)


def _first_takedown(ctx: MatchContext, before_ms: int) -> int | None:
    """Timestamp of the player's first kill/assist at or before ``before_ms``."""
    pid = ctx.participant_id
    for frame in ctx.timeline["info"]["frames"]:
        for ev in frame.get("events", []):
            if (ev.get("type") == "CHAMPION_KILL"
                    and ev.get("timestamp", 0) <= before_ms
                    and (ev.get("killerId") == pid
                         or pid in ev.get("assistingParticipantIds", []))):
                return ev["timestamp"]
    return None


@register("jungle_first_clear")
def jungle_first_clear(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if the jungler cleared enough camps early and made a full first
    back: jungle CS at ``minute`` >= ``min_jungle_cs`` AND gold spent on the
    first shopping trip >= ``min_first_back_spend`` (guide: full clear, then
    recall and buy an 800/900g component).

    Not evaluated when the jungler already has a kill/assist by
    ``exempt_if_takedown_by_minute``: an early gank path that converts is a
    correct alternative to a full clear, not a deviation.
    """
    exempt_min = params.get("exempt_if_takedown_by_minute")
    if exempt_min is not None:
        t = _first_takedown(ctx, int(exempt_min) * 60_000)
        if t is not None:
            mm, ss = divmod(t // 1000, 60)
            return RuleResult(
                "jungle_first_clear", True, 1.0,
                f"{mm}:{ss:02d} に序盤ガンクでキル/アシスト — フルクリア判定は対象外。",
                [Evidence(detail="early takedown", timestamp_ms=t)])

    minute = int(params.get("minute", 4))
    min_cs = int(params.get("min_jungle_cs", 24))
    min_spend = int(params.get("min_first_back_spend", 800))
    grace_ms = int(params.get("start_buy_grace_s", 90)) * 1000
    cluster_ms = int(params.get("trip_window_s", 60)) * 1000

    frames = ctx.timeline["info"]["frames"]
    pid = ctx.participant_id
    jg_cs = frames[min(minute, len(frames) - 1)]["participantFrames"][str(pid)].get(
        "jungleMinionsKilled", 0)
    cs_ok = jg_cs >= min_cs
    parts = [f"{minute}分時点のJG CS {jg_cs}（目標 {min_cs}以上）"]
    evidence = [Evidence(detail=f"jungle CS={jg_cs}", timestamp_ms=minute * 60_000)]

    trip = _first_back(ctx, grace_ms, cluster_ms)
    if trip is None:
        spend_ok, spend_score = False, 0.0
        parts.append("初回帰還の購入が見つからない")
    else:
        spent = _gold_spent(frames, pid, *trip)
        spend_ok = spent >= min_spend
        spend_score = min(spent / min_spend, 1.0) if min_spend else 1.0
        mm, ss = divmod(trip[0] // 1000, 60)
        parts.append(f"初回帰還 {mm}:{ss:02d} で約 {spent}G 購入（目標 {min_spend}G以上）")
        evidence.append(Evidence(detail=f"first back spend≈{spent}", timestamp_ms=trip[0]))

    passed = cs_ok and spend_ok
    score = (min(jg_cs / min_cs, 1.0) if min_cs else 1.0) * 0.5 + spend_score * 0.5
    return RuleResult("jungle_first_clear", passed, score, "／".join(parts) + "。", evidence)
