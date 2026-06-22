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


@pytest.fixture
def make_ctx():
    """Factory for a 2-player (me vs same-role opponent) match context.

    Used by itemization/laning rule tests. `boot_ids` are ITEM_PURCHASED by
    the player at frame 0; lane stats are read at `minute`.
    """

    def _make(*, phys=7000, magic=2000, true=1000, boot_ids=(),
              me_cs=97, opp_cs=109, me_gold=5421, opp_gold=5931,
              me_level=9, opp_level=9, n_frames=17):
        me = {"participantId": 1, "teamId": 100, "teamPosition": "BOTTOM",
              "championName": "Sivir", "physicalDamageTaken": phys,
              "magicDamageTaken": magic, "trueDamageTaken": true}
        opp = {"participantId": 6, "teamId": 200, "teamPosition": "BOTTOM",
               "championName": "Senna", "physicalDamageTaken": 0,
               "magicDamageTaken": 0, "trueDamageTaken": 0}

        def pf(cs, gold, level):
            return {"minionsKilled": cs, "jungleMinionsKilled": 0,
                    "totalGold": gold, "level": level,
                    "position": {"x": 0, "y": 0}}

        frames = []
        for i in range(n_frames):
            events = [
                {"type": "ITEM_PURCHASED", "participantId": 1,
                 "itemId": b, "timestamp": 60_000}
                for b in (boot_ids if i == 0 else ())
            ]
            frames.append({
                "timestamp": i * 60_000,
                "participantFrames": {
                    "1": pf(me_cs, me_gold, me_level),
                    "6": pf(opp_cs, opp_gold, opp_level),
                },
                "events": events,
            })

        return MatchContext(
            match_id="T",
            puuid="p1",
            participant_id=1,
            match={"metadata": {"participants": ["p1", "p2", "p3", "p4", "p5", "p6"]},
                   "info": {"participants": [me, opp]}},
            timeline={"info": {"frames": frames}},
        )

    return _make
