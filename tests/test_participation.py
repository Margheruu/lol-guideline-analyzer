"""Unit tests for kill_participation."""
from __future__ import annotations

from src.rules.base import MatchContext
from src.rules.participation import kill_participation


def _ctx(participant: dict, teams: list[dict]) -> MatchContext:
    return MatchContext(
        match_id="m", puuid="p", participant_id=1,
        match={"info": {"participants": [participant], "teams": teams}},
        timeline={"info": {"frames": []}},
    )


def test_uses_challenges_kill_participation_when_present():
    participant = {"participantId": 1, "teamId": 100, "kills": 3, "assists": 2,
                   "challenges": {"killParticipation": 0.6}}
    teams = [{"teamId": 100, "objectives": {"champion": {"kills": 20}}}]
    res = kill_participation(_ctx(participant, teams), {"min_participation": 0.5})
    assert res.passed is True
    assert "60%" in res.message


def test_falls_back_to_manual_ratio_when_challenges_missing():
    participant = {"participantId": 1, "teamId": 100, "kills": 1, "assists": 1}
    teams = [{"teamId": 100, "objectives": {"champion": {"kills": 10}}}]
    # (1+1)/10 = 0.2 < 0.5 -> fail.
    res = kill_participation(_ctx(participant, teams), {"min_participation": 0.5})
    assert res.passed is False


def test_zero_team_kills_is_zero_participation():
    participant = {"participantId": 1, "teamId": 100, "kills": 0, "assists": 0}
    teams = [{"teamId": 100, "objectives": {"champion": {"kills": 0}}}]
    res = kill_participation(_ctx(participant, teams), {"min_participation": 0.5})
    assert res.passed is False
