"""Core (completed legendary) item purchases, for build-timing comparison.

"Core" = a purchasable, finished item (not a component of something else),
costing >= 2000g, excluding boots / consumables / trinkets, on Summoner's Rift.
Item metadata comes from Data Dragon (`ddragon.item_data`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ingest.ddragon import item_data


@dataclass
class ItemBuy:
    timestamp_ms: int
    item_id: int
    name: str


def is_core(item_id: int, meta: dict[str, Any]) -> bool:
    m = meta.get(str(item_id))
    if not m:
        return False
    gold = m.get("gold", {})
    tags = m.get("tags", [])
    if not gold.get("purchasable", False):
        return False
    if m.get("into"):  # a component that builds into something else
        return False
    if gold.get("total", 0) < 2000:
        return False
    if {"Consumable", "Boots", "Trinket"} & set(tags):
        return False
    return bool(m.get("maps", {}).get("11", True))


def core_items_for(ctx: Any, participant_id: int,
                   item_meta: dict[str, Any] | None = None) -> list[ItemBuy]:
    """Ordered first-purchase times of the player's completed core items."""
    meta = item_meta if item_meta is not None else item_data()
    seen: set[int] = set()
    out: list[ItemBuy] = []
    for frame in ctx.timeline["info"]["frames"]:
        for ev in frame.get("events", []):
            if (ev.get("type") != "ITEM_PURCHASED"
                    or ev.get("participantId") != participant_id):
                continue
            iid = ev.get("itemId")
            if iid in seen or not is_core(iid, meta):
                continue
            seen.add(iid)
            name = meta.get(str(iid), {}).get("name", str(iid))
            out.append(ItemBuy(ev.get("timestamp", 0), iid, name))
    return out
