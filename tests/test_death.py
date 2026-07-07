"""Unit tests for death-analysis rules."""
from __future__ import annotations

from src.analysis.deaths import deaths_for
from src.rules.death import (
    death_cause_summary,
    frontmost_deaths,
    isolated_deaths,
    low_hp_deaths,
)


def test_deaths_for_builds_records(make_death_ctx):
    ctx = make_death_ctx([{"minute": 12, "pos": (11000, 11000),
                           "hp_pct": 0.2, "ally_near": True}])
    recs = deaths_for(ctx)
    assert len(recs) == 1
    assert recs[0].killer_champion == "Yorick"
    assert recs[0].top_damage_source == "Yorick"
    assert abs(recs[0].health_pct_before - 0.2) < 0.01


def test_isolated_death_flagged(make_death_ctx):
    ctx = make_death_ctx([{"minute": 12, "pos": (11000, 11000),
                           "hp_pct": 0.8, "ally_near": False}])
    res = isolated_deaths(ctx, {"max_deaths": 0})
    assert res.passed is False
    assert len(res.evidence) == 1


def test_death_with_ally_not_isolated(make_death_ctx):
    ctx = make_death_ctx([{"minute": 12, "pos": (11000, 11000),
                           "hp_pct": 0.8, "ally_near": True}])
    res = isolated_deaths(ctx, {"max_deaths": 0})
    assert res.passed is True


def test_low_hp_death_flagged(make_death_ctx):
    ctx = make_death_ctx([{"minute": 10, "pos": (8000, 8000),
                           "hp_pct": 0.2, "ally_near": True}])
    res = low_hp_deaths(ctx, {"health_pct": 0.35, "max_deaths": 0})
    assert res.passed is False


def test_high_hp_death_ok(make_death_ctx):
    ctx = make_death_ctx([{"minute": 10, "pos": (8000, 8000),
                           "hp_pct": 0.9, "ally_near": True}])
    res = low_hp_deaths(ctx, {"health_pct": 0.35, "max_deaths": 0})
    assert res.passed is True


def test_frontmost_death_flagged(make_death_ctx):
    # Position past the enemy base (14400,14400) so the ally (offset +500 on
    # both axes) ends up *farther* from base than me -> I'm the front line.
    ctx = make_death_ctx([{"minute": 12, "pos": (16000, 16000),
                           "hp_pct": 0.8, "ally_near": True}])
    res = frontmost_deaths(ctx, {"max_deaths": 0})
    assert res.passed is False
    assert len(res.evidence) == 1


def test_not_frontmost_when_ally_more_forward(make_death_ctx):
    # Ally offset (+500,+500) is closer to the enemy base than me here -> the
    # ally engaged first, not me.
    ctx = make_death_ctx([{"minute": 12, "pos": (11000, 11000),
                           "hp_pct": 0.8, "ally_near": True}])
    res = frontmost_deaths(ctx, {"max_deaths": 0})
    assert res.passed is True


def test_death_cause_summary_reports_breakdown(make_death_ctx):
    ctx = make_death_ctx([
        {"minute": 10, "pos": (8000, 8000), "hp_pct": 0.9, "ally_near": True},
        {"minute": 14, "pos": (8000, 8000), "hp_pct": 0.5, "ally_near": True},
    ])
    res = death_cause_summary(ctx, {})
    assert res.passed is True
    assert "Yorick" in res.message
    assert len(res.evidence) == 2


def test_death_cause_summary_no_deaths(make_ctx):
    # make_ctx's 2-player fixture has no CHAMPION_KILL events at all.
    ctx = make_ctx()
    res = death_cause_summary(ctx, {})
    assert res.passed is True
    assert "デスなし" in res.message
