"""Shared fixtures: small synthetic timelines so rules are testable offline."""
from __future__ import annotations

import pytest

from src.rules.base import MatchContext


def _frame(minute: int, cs: int = 0, events: list | None = None) -> dict:
    return {
        "timestamp": minute * 60_000,
        "participantFrames": {
            "1": {
                "minionsKilled": cs,
                "jungleMinionsKilled": 0,
                "position": {"x": 1000, "y": 1000},
                "currentGold": 500,
            }
        },
        "events": events or [],
    }


@pytest.fixture
def ctx() -> MatchContext:
    """Player 1: dies once at 5:00, has 75 CS by minute 10."""
    death = {
        "type": "CHAMPION_KILL",
        "victimId": 1,
        "killerId": 6,
        "timestamp": 5 * 60_000,
        "position": {"x": 4200, "y": 4200},
    }
    frames = [_frame(m, cs=m * 8, events=[death] if m == 5 else None) for m in range(11)]
    timeline = {"info": {"frames": frames}}
    return MatchContext(
        match_id="TEST_1",
        puuid="puuid-1",
        participant_id=1,
        match={"metadata": {"participants": ["puuid-1"]}},
        timeline=timeline,
    )
