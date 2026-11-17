"""Unit tests for match_label (match picker labels)."""
from __future__ import annotations

from src.analysis.match_summary import match_label


def _match(queue=400, mode="CLASSIC", pos="MIDDLE", win=False):
    return {"info": {
        "gameCreation": 1763304780000,  # 2025-11-16 23:53 JST
        "queueId": queue, "gameMode": mode,
        "participants": [
            {"puuid": "other", "championName": "TahmKench", "teamPosition": "BOTTOM", "win": True},
            {"puuid": "me", "championName": "Hwei", "teamPosition": pos, "win": win},
        ]}}


def test_label_uses_the_players_own_champion_in_jst():
    label = match_label(_match(), "me", {"Hwei": "フェイ"})
    assert label == "11/16 23:53｜ノーマル｜フェイ（MID）｜敗北"


def test_unknown_queue_and_missing_role_fall_back_gracefully():
    label = match_label(_match(queue=1700, mode="CHERRY", pos=""), "me")
    assert label.endswith("その他（CHERRY）｜Hwei｜敗北")


def test_player_not_in_match_still_labels_date_and_queue():
    assert match_label(_match(), "nobody") == "11/16 23:53｜ノーマル"
