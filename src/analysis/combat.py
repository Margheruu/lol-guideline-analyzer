"""Takedowns (kills + assists) by the player, for plotting/participation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Takedown:
    timestamp_ms: int
    position: dict[str, float]
    kind: str  # "kill" | "assist"


def takedowns_for(ctx: Any) -> list[Takedown]:
    """Kills (player is killer) and assists (player assisted) with positions."""
    pid = ctx.participant_id
    out: list[Takedown] = []
    for frame in ctx.timeline["info"]["frames"]:
        for ev in frame.get("events", []):
            if ev.get("type") != "CHAMPION_KILL":
                continue
            pos = ev.get("position", {}) or {}
            ts = ev.get("timestamp", 0)
            if ev.get("killerId") == pid:
                out.append(Takedown(ts, pos, "kill"))
            elif pid in (ev.get("assistingParticipantIds") or []):
                out.append(Takedown(ts, pos, "assist"))
    return out
