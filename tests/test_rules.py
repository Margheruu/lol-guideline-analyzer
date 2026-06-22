"""Unit tests for the example rules."""
from __future__ import annotations

from src.rules.examples import cs_at_10, deaths_before_minute


def test_deaths_before_minute_passes_under_limit(ctx):
    # One death at 5:00; limit 1 before minute 8 -> pass.
    res = deaths_before_minute(ctx, {"before_minute": 8, "max_deaths": 1})
    assert res.passed is True
    assert len(res.evidence) == 1


def test_deaths_before_minute_fails_over_limit(ctx):
    # One death at 5:00; limit 0 before minute 8 -> fail.
    res = deaths_before_minute(ctx, {"before_minute": 8, "max_deaths": 0})
    assert res.passed is False


def test_deaths_window_excludes_later_deaths(ctx):
    # Death is at 5:00; window ends at 4:00 -> no deaths counted.
    res = deaths_before_minute(ctx, {"before_minute": 4, "max_deaths": 0})
    assert res.passed is True
    assert res.evidence == []


def test_cs_at_10_meets_target(ctx):
    # Minute 10 frame has 10*8 = 80 CS; target 70 -> pass.
    res = cs_at_10(ctx, {"minute": 10, "min_cs": 70})
    assert res.passed is True
    assert res.score == 1.0


def test_cs_at_10_below_target(ctx):
    res = cs_at_10(ctx, {"minute": 10, "min_cs": 200})
    assert res.passed is False
    assert 0.0 <= res.score < 1.0
