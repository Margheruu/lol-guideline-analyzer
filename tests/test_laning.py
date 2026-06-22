"""Unit tests for not_behind_at_minute."""
from __future__ import annotations

from src.rules.laning import not_behind_at_minute


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
