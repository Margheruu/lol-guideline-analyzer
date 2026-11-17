"""Unit tests for participant_id_for (puuid -> timeline participant id)."""
from __future__ import annotations

import pytest

from src.eval.runner import participant_id_for


def _match(meta_order: list[str]) -> dict:
    """10 players p1..p10 with participantId 1..10; metadata in `meta_order`."""
    return {
        "metadata": {"matchId": "JP1_TEST", "participants": meta_order},
        "info": {"participants": [{"participantId": i, "puuid": f"p{i}"} for i in range(1, 11)]},
    }


def test_ignores_metadata_order():
    # Riot now returns metadata.participants shuffled relative to participantId
    # (seen from 2026-11-12, e.g. JP1_613117144). p3 sits at index 4 here.
    shuffled = ["p5", "p1", "p2", "p4", "p3", "p6", "p8", "p10", "p7", "p9"]
    assert participant_id_for(_match(shuffled), "p3") == 3
    assert participant_id_for(_match(shuffled), "p5") == 5


def test_aligned_metadata_still_works():
    aligned = [f"p{i}" for i in range(1, 11)]
    assert participant_id_for(_match(aligned), "p9") == 9


def test_unknown_puuid_raises():
    with pytest.raises(ValueError):
        participant_id_for(_match([f"p{i}" for i in range(1, 11)]), "nobody")


def test_out_of_order_info_raises_instead_of_picking_someone_else():
    m = _match([f"p{i}" for i in range(1, 11)])
    m["info"]["participants"].reverse()
    with pytest.raises(ValueError):
        participant_id_for(m, "p3")
