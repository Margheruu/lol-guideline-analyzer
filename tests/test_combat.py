"""Unit tests for takedown extraction and the coordinate transform."""
from __future__ import annotations

from src.analysis.combat import takedowns_for
from src.rules.base import MatchContext
from src.viz.map_plot import MAP_MAX, to_pixel


def _ctx(events):
    return MatchContext(
        match_id="m", puuid="p", participant_id=1,
        match={"info": {"participants": [{"participantId": 1, "teamId": 100}]}},
        timeline={"info": {"frames": [{"events": events}]}},
    )


def test_takedowns_kill_and_assist_only():
    ctx = _ctx([
        {"type": "CHAMPION_KILL", "killerId": 1,
         "position": {"x": 100, "y": 200}, "timestamp": 1000},
        {"type": "CHAMPION_KILL", "killerId": 5,
         "assistingParticipantIds": [1],
         "position": {"x": 300, "y": 400}, "timestamp": 2000},
        {"type": "CHAMPION_KILL", "killerId": 7, "victimId": 1,
         "position": {"x": 0, "y": 0}, "timestamp": 3000},  # our death: excluded
    ])
    kinds = sorted(t.kind for t in takedowns_for(ctx))
    assert kinds == ["assist", "kill"]


def test_to_pixel_flips_y():
    # game (0, MAX) is the top-left -> pixel (0, 0)
    assert to_pixel({"x": 0, "y": MAP_MAX}, 100, 100) == (0.0, 0.0)
    # game (MAX, 0) is the bottom-right -> pixel (w, h)
    x, y = to_pixel({"x": MAP_MAX, "y": 0}, 100, 100)
    assert abs(x - 100) < 1e-6 and abs(y - 100) < 1e-6
