"""Unit tests for laning rules."""
from __future__ import annotations

from src.rules.laning import cs_per_minute, not_behind_at_minute


def test_cs_per_minute_meets_target(make_ctx):
    # 120 CS at minute 15 -> 8.0/min >= 7.5 -> pass.
    ctx = make_ctx(me_cs=120)
    res = cs_per_minute(ctx, {"minute": 15, "min_cs_per_min": 7.5})
    assert res.passed is True


def test_cs_per_minute_below_target(make_ctx):
    # 97 CS at minute 15 -> ~6.5/min < 7.5 -> fail.
    ctx = make_ctx(me_cs=97)
    res = cs_per_minute(ctx, {"minute": 15, "min_cs_per_min": 7.5})
    assert res.passed is False
    assert 0.0 <= res.score < 1.0


def test_behind_beyond_deficit_fails(make_ctx):
    # -510 gold at 15:00 with a 500 tolerance -> fail.
    ctx = make_ctx(me_gold=5421, opp_gold=5931)
    res = not_behind_at_minute(ctx, {"minute": 15, "max_gold_deficit": 500})
    assert res.passed is False


def test_even_passes(make_ctx):
    ctx = make_ctx(me_gold=6000, opp_gold=6000)
    res = not_behind_at_minute(ctx, {"minute": 15, "max_gold_deficit": 500})
    assert res.passed is True


def test_ahead_passes(make_ctx):
    ctx = make_ctx(me_cs=120, opp_cs=90, me_gold=7000, opp_gold=6000)
    res = not_behind_at_minute(ctx, {"minute": 15, "max_gold_deficit": 500})
    assert res.passed is True
    assert "+1000" in res.message  # gold diff shown


def test_cs_level_deficit_not_evaluated_by_default(make_ctx):
    # max_cs_deficit / max_level_deficit unset -> only gold matters (back-compat).
    ctx = make_ctx(me_gold=6000, opp_gold=6000, me_cs=50, opp_cs=150,
                    me_level=5, opp_level=12)
    res = not_behind_at_minute(ctx, {"minute": 15, "max_gold_deficit": 500})
    assert res.passed is True


def test_cs_deficit_fails_when_configured(make_ctx):
    # Gold is even but CS deficit (-20) exceeds max_cs_deficit (10) -> fail.
    ctx = make_ctx(me_gold=6000, opp_gold=6000, me_cs=90, opp_cs=110)
    res = not_behind_at_minute(
        ctx, {"minute": 15, "max_gold_deficit": 500, "max_cs_deficit": 10})
    assert res.passed is False
    assert "CS" in res.message


def test_cs_deficit_within_tolerance_passes(make_ctx):
    ctx = make_ctx(me_gold=6000, opp_gold=6000, me_cs=100, opp_cs=105)
    res = not_behind_at_minute(
        ctx, {"minute": 15, "max_gold_deficit": 500, "max_cs_deficit": 10})
    assert res.passed is True


def test_level_deficit_fails_when_configured(make_ctx):
    ctx = make_ctx(me_gold=6000, opp_gold=6000, me_level=8, opp_level=10)
    res = not_behind_at_minute(
        ctx, {"minute": 15, "max_gold_deficit": 500, "max_level_deficit": 1})
    assert res.passed is False
    assert "レベル" in res.message
