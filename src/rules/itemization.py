"""Itemization rules.

`boots_type_match` is intentionally high-precision: it only judges a defensive
boot's *resist type* against the damage the player actually took. Offensive
boots (e.g. Berserker's Greaves) or no boots are reported as "not evaluated" —
v1 does not try to auto-judge whether going defensive was the right call.

Boot resist type is derived from Data Dragon item tags (`Armor` / `SpellBlock`)
rather than a hardcoded item-id list, so any defensive boot Riot adds later is
picked up automatically without a code change.
"""
from __future__ import annotations

from typing import Any

from src.ingest.ddragon import item_data

from .base import Evidence, MatchContext, RuleResult
from .registry import register

# Canonical item id to suggest per resist type (used only for the message).
_SUGGEST_ID = {"armor": 3047, "mr": 3111}


def _me(ctx: MatchContext) -> dict[str, Any]:
    return ctx.match["info"]["participants"][ctx.participant_id - 1]


def _purchased_item_ids(ctx: MatchContext) -> list[int]:
    ids: list[int] = []
    for frame in ctx.timeline["info"]["frames"]:
        for ev in frame.get("events", []):
            if (ev.get("type") == "ITEM_PURCHASED"
                    and ev.get("participantId") == ctx.participant_id):
                ids.append(ev.get("itemId"))
    return ids


def _boot_resist_type(item_id: int, meta: dict[str, Any]) -> str | None:
    """Classify a boot's resist type from its tags, or None if it isn't a
    defensive boot (offensive boots, tier-1 boots, CDR boots, etc.)."""
    m = meta.get(str(item_id))
    if not m or "Boots" not in m.get("tags", []):
        return None
    tags = set(m.get("tags", []))
    if "Armor" in tags:
        return "armor"
    if "SpellBlock" in tags:
        return "mr"
    return None


def _name(item_id: int, meta: dict[str, Any]) -> str:
    return meta.get(str(item_id), {}).get("name", str(item_id))


@register("boots_type_match")
def boots_type_match(
    ctx: MatchContext,
    params: dict[str, Any],
    item_meta: dict[str, Any] | None = None,
) -> RuleResult:
    """If a defensive boot was built, is its resist type right for the threat?

    ``item_meta`` overrides Data Dragon lookup (for tests); production calls
    (via the registry) always pass only ``(ctx, params)`` and fetch live data.
    """
    threshold = float(params.get("threshold", 0.6))
    meta = item_meta if item_meta is not None else item_data()
    me = _me(ctx)
    pt = me.get("physicalDamageTaken", 0)
    mt = me.get("magicDamageTaken", 0)
    truet = me.get("trueDamageTaken", 0)
    total = pt + mt + truet
    if total == 0:
        return RuleResult("boots_type_match", True, 1.0,
                          "被ダメージなし。評価対象外。", [])

    phys, magic = pt / total, mt / total
    profile = f"被ダメージ 物理{phys:.0%} / 魔法{magic:.0%}"
    suggest_type = "armor" if phys >= magic else "mr"
    suggest_name = _name(_SUGGEST_ID[suggest_type], meta)

    built = [(iid, _boot_resist_type(iid, meta)) for iid in _purchased_item_ids(ctx)]
    built = [(iid, t) for iid, t in built if t is not None]
    if not built:
        return RuleResult(
            "boots_type_match", True, 1.0,
            f"防御靴なし。評価対象外（{profile}）。防御靴を積むなら: {suggest_name}。",
            [Evidence(detail=profile)],
        )

    built_id, built_type = built[-1]
    built_name = _name(built_id, meta)
    expected = "armor" if phys >= threshold else ("mr" if magic >= threshold else None)
    if expected is None:
        return RuleResult("boots_type_match", True, 1.0,
                          f"ダメージは均衡（{profile}）。どちらの耐性靴でも可。",
                          [Evidence(detail=profile)])

    passed = built_type == expected
    msg = (f"{built_name} を装備（{profile}）— "
           + ("耐性型は適切。"
              if passed else f"不一致: 推奨は {_name(_SUGGEST_ID[expected], meta)}。"))
    return RuleResult("boots_type_match", passed, 1.0 if passed else 0.0, msg,
                      [Evidence(detail=profile)])
