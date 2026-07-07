"""Unit tests for wards_per_interval."""
from __future__ import annotations

from src.rules.base import MatchContext
from src.rules.vision import wards_per_interval


def _ctx(events: list[dict]) -> MatchContext:
    return MatchContext(
        match_id="m", puuid="p", participant_id=1,
        match={"info": {"participants": []}},
        timeline={"info": {"frames": [{"timestamp": 0, "events": events}]}},
    )


def test_meets_target_pace():
    # 5 wards by 15:00, interval=3min -> 5 intervals -> 1.0/interval -> pass.
    events = [{"type": "WARD_PLACED", "creatorId": 1, "timestamp": m * 60_000}
              for m in (1, 4, 7, 10, 13)]
    res = wards_per_interval(
        _ctx(events),
        {"interval_minutes": 3, "min_wards_per_interval": 1, "through_minute": 15},
    )
    assert res.passed is True


def test_below_target_pace():
    events = [{"type": "WARD_PLACED", "creatorId": 1, "timestamp": t}
              for t in (60_000, 120_000)]  # only 2 wards total
    res = wards_per_interval(
        _ctx(events),
        {"interval_minutes": 3, "min_wards_per_interval": 1, "through_minute": 15},
    )
    assert res.passed is False


def test_ignores_other_players_and_late_wards():
    events = [
        {"type": "WARD_PLACED", "creatorId": 2, "timestamp": 60_000},       # other player
        {"type": "WARD_PLACED", "creatorId": 1, "timestamp": 20 * 60_000},  # after cutoff
    ]
    res = wards_per_interval(_ctx(events), {"through_minute": 15})
    assert "合計 0本" in res.message
