"""Unit tests for jungle_first_clear."""
from __future__ import annotations

from src.rules.base import MatchContext
from src.rules.jungle import jungle_first_clear

PARAMS = {"minute": 4, "min_jungle_cs": 24, "min_first_back_spend": 800}


def _ctx(jg_cs_at_4: int, back_s: int | None, spend: int) -> MatchContext:
    """Jungler (pid 1) earns 200g/min; optionally buys `spend` gold of items
    at `back_s` seconds (plus a starting buy at 0:05)."""
    frames = []
    current = total = 500
    for i in range(8):
        if i:
            current += 200
            total += 200
        events = [{"type": "ITEM_PURCHASED", "participantId": 1, "timestamp": 5_000}] if i == 0 else []
        if back_s is not None and i == back_s // 60:
            events.append({"type": "ITEM_PURCHASED", "participantId": 1,
                           "timestamp": back_s * 1000})
        frames.append({"timestamp": i * 60_000, "events": events,
                       "participantFrames": {"1": {
                           "jungleMinionsKilled": jg_cs_at_4 if i >= 4 else i * 6,
                           "currentGold": current, "totalGold": total}}})
        if back_s is not None and i == back_s // 60:
            current -= spend  # spent between this frame and the next
    return MatchContext("m", "p", 1, {"info": {"participants": []}},
                        {"info": {"frames": frames}})


def test_full_clear_and_full_back_passes():
    res = jungle_first_clear(_ctx(26, back_s=230, spend=900), PARAMS)
    assert res.passed, res.message
    assert "約 900G" in res.message


def test_early_cheap_back_fails():
    res = jungle_first_clear(_ctx(26, back_s=150, spend=350), PARAMS)
    assert not res.passed


def test_slow_clear_fails():
    res = jungle_first_clear(_ctx(18, back_s=230, spend=900), PARAMS)
    assert not res.passed


def test_no_back_found_fails():
    res = jungle_first_clear(_ctx(26, back_s=None, spend=0), PARAMS)
    assert not res.passed and "見つからない" in res.message


def test_early_gank_takedown_exempts_full_clear_check():
    ctx = _ctx(18, back_s=150, spend=350)  # would fail on both checks
    ctx.timeline["info"]["frames"][2]["events"].append(
        {"type": "CHAMPION_KILL", "killerId": 6, "victimId": 7,
         "assistingParticipantIds": [1], "timestamp": 140_000})
    params = {**PARAMS, "exempt_if_takedown_by_minute": 4}
    res = jungle_first_clear(ctx, params)
    assert res.passed and "対象外" in res.message
    # Without the exemption param the same match still fails.
    assert not jungle_first_clear(ctx, PARAMS).passed
