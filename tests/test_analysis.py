"""Unit tests for lane series and core-item extraction."""
from __future__ import annotations

from src.analysis.items import core_items_for, is_core
from src.analysis.lane_series import cs_series
from src.rules.base import MatchContext

ITEM_META = {
    "3153": {"name": "ボッ", "gold": {"total": 3200, "purchasable": True},
             "tags": ["Damage"], "maps": {"11": True}},  # core legendary
    "1038": {"name": "BFソード", "gold": {"total": 1300, "purchasable": True},
             "into": ["3153"], "tags": ["Damage"], "maps": {"11": True}},  # component
    "3047": {"name": "鋼の靴", "gold": {"total": 1100, "purchasable": True},
             "tags": ["Boots"], "maps": {"11": True}},  # boots
    "2003": {"name": "ポーション", "gold": {"total": 50, "purchasable": True},
             "tags": ["Consumable"], "maps": {"11": True}},  # consumable
}


def test_cs_series_tracks_both(make_ctx):
    rows = cs_series(make_ctx(me_cs=97, opp_cs=109))
    assert len(rows) == 17
    assert rows[15]["self"] == 97
    assert rows[15]["opponent"] == 109


def test_is_core_classification():
    assert is_core(3153, ITEM_META) is True          # legendary
    assert is_core(1038, ITEM_META) is False         # component (into)
    assert is_core(3047, ITEM_META) is False         # boots
    assert is_core(2003, ITEM_META) is False         # consumable


def test_core_items_for_picks_completed_only():
    ctx = MatchContext(
        match_id="m", puuid="p", participant_id=1,
        match={"info": {"participants": [{"participantId": 1, "teamId": 100}]}},
        timeline={"info": {"frames": [{"events": [
            {"type": "ITEM_PURCHASED", "participantId": 1, "itemId": 1038, "timestamp": 1000},
            {"type": "ITEM_PURCHASED", "participantId": 1, "itemId": 3153, "timestamp": 2000},
            {"type": "ITEM_PURCHASED", "participantId": 1, "itemId": 3047, "timestamp": 3000},
            {"type": "ITEM_PURCHASED", "participantId": 2, "itemId": 3153, "timestamp": 1500},
        ]}]}},
    )
    core = core_items_for(ctx, 1, item_meta=ITEM_META)
    assert [c.item_id for c in core] == [3153]
    assert core[0].timestamp_ms == 2000
