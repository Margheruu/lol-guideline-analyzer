"""Itemization rules.

`boots_type_match` is intentionally high-precision: it only judges a defensive
boot's *resist type* against the damage the player actually took. Offensive
boots (e.g. Berserker's Greaves) or no boots are reported as "not evaluated" —
v1 does not try to auto-judge whether going defensive was the right call.
"""
from __future__ import annotations

from typing import Any

from .base import Evidence, MatchContext, RuleResult
from .registry import register

# Tier-2 defensive boots -> resist type. Extend via Data Dragon item tags later.
DEFENSIVE_BOOTS = {3047: "armor", 3111: "mr"}
_LABEL = {"armor": "Plated Steelcaps", "mr": "Mercury's Treads"}


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


@register("boots_type_match")
def boots_type_match(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """If a defensive boot was built, is its resist type right for the threat?"""
    threshold = float(params.get("threshold", 0.6))
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
    suggest = _LABEL["armor"] if phys >= magic else _LABEL["mr"]

    built = [DEFENSIVE_BOOTS[i] for i in _purchased_item_ids(ctx)
             if i in DEFENSIVE_BOOTS]
    if not built:
        return RuleResult(
            "boots_type_match", True, 1.0,
            f"防御靴なし。評価対象外（{profile}）。防御靴を積むなら: {suggest}。",
            [Evidence(detail=profile)],
        )

    built_type = built[-1]
    expected = "armor" if phys >= threshold else ("mr" if magic >= threshold else None)
    if expected is None:
        return RuleResult("boots_type_match", True, 1.0,
                          f"ダメージは均衡（{profile}）。どちらの耐性靴でも可。",
                          [Evidence(detail=profile)])

    passed = built_type == expected
    msg = (f"{_LABEL[built_type]} を装備（{profile}）— "
           + ("耐性型は適切。"
              if passed else f"不一致: 推奨は {_LABEL[expected]}。"))
    return RuleResult("boots_type_match", passed, 1.0 if passed else 0.0, msg,
                      [Evidence(detail=profile)])
