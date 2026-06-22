"""Death analysis — the PDF's most-repeated theme ("analyze your deaths").

Builds a structured record per death from the timeline. Decoupled from the
rules layer (ctx is duck-typed) so it can also feed visualization.

Caveats (60s sampling): the kill event position is exact, but teammates'
positions and the victim's HP come from the nearest <=death frame, so they can
be up to ~60s stale. Treat "allies nearby" / "HP before" as approximate.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any

# Approx enemy nexus position by team id (Summoner's Rift ~ 0..15000).
_ENEMY_BASE = {100: (14400, 14400), 200: (1500, 1500)}


@dataclass
class DeathRecord:
    timestamp_ms: int
    position: dict[str, float]
    health_pct_before: float | None
    killer_champion: str | None
    top_damage_source: str | None
    allies_nearby: int
    is_frontmost: bool


def _by_id(match: dict[str, Any], key: str) -> dict[int, Any]:
    return {p["participantId"]: p.get(key) for p in match["info"]["participants"]}


def _nearest_frame(frames: list[dict], ts: int) -> dict:
    return frames[min(ts // 60_000, len(frames) - 1)]


def _top_source(damage_received: list[dict]) -> str | None:
    if not damage_received:
        return None
    agg: dict[str, int] = {}
    for d in damage_received:
        name = d.get("name", "?")
        agg[name] = agg.get(name, 0) + (
            d.get("physicalDamage", 0) + d.get("magicDamage", 0)
            + d.get("trueDamage", 0)
        )
    return max(agg, key=agg.get) if agg else None


def deaths_for(ctx: Any, nearby_radius: int = 2000) -> list[DeathRecord]:
    """Return a DeathRecord for each time the player was the kill victim."""
    pid = ctx.participant_id
    teams = _by_id(ctx.match, "teamId")
    champs = _by_id(ctx.match, "championName")
    my_team = teams.get(pid)
    base = _ENEMY_BASE.get(my_team, (7500, 7500))
    frames = ctx.timeline["info"]["frames"]

    records: list[DeathRecord] = []
    for frame in frames:
        for ev in frame.get("events", []):
            if ev.get("type") != "CHAMPION_KILL" or ev.get("victimId") != pid:
                continue
            ts = ev.get("timestamp", 0)
            pos = ev.get("position", {}) or {}
            pf = _nearest_frame(frames, ts)["participantFrames"]

            stats = pf.get(str(pid), {}).get("championStats", {})
            hp, hp_max = stats.get("health"), stats.get("healthMax")
            hp_pct = hp / hp_max if hp is not None and hp_max else None

            killer = champs.get(ev.get("killerId")) if ev.get("killerId") else None
            top = _top_source(ev.get("victimDamageReceived") or [])

            near = 0
            base_dists = [hypot(pos.get("x", 0) - base[0], pos.get("y", 0) - base[1])]
            for opid_str, opf in pf.items():
                opid = int(opid_str)
                if opid == pid or teams.get(opid) != my_team:
                    continue
                ap = opf.get("position", {})
                if hypot(ap.get("x", 0) - pos.get("x", 0),
                         ap.get("y", 0) - pos.get("y", 0)) <= nearby_radius:
                    near += 1
                    base_dists.append(
                        hypot(ap.get("x", 0) - base[0], ap.get("y", 0) - base[1]))

            frontmost = near > 0 and base_dists[0] == min(base_dists)
            records.append(DeathRecord(ts, pos, hp_pct, killer, top, near, frontmost))
    return records
