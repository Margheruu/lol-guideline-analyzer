"""Per-minute lane series (player vs same-role opponent) for charts."""
from __future__ import annotations

from typing import Any


def _me(ctx: Any) -> dict[str, Any]:
    return ctx.match["info"]["participants"][ctx.participant_id - 1]


def opponent_of(ctx: Any, me: dict[str, Any]) -> dict[str, Any] | None:
    pos = me.get("teamPosition")
    if not pos:
        return None
    for p in ctx.match["info"]["participants"]:
        if p["teamId"] != me["teamId"] and p.get("teamPosition") == pos:
            return p
    return None


def _cs(pf: dict[str, Any]) -> int:
    return pf.get("minionsKilled", 0) + pf.get("jungleMinionsKilled", 0)


def cs_series(ctx: Any) -> list[dict[str, int]]:
    """CS per minute for the player and (if found) the same-role opponent."""
    me = _me(ctx)
    opp = opponent_of(ctx, me)
    rows: list[dict[str, int]] = []
    for i, frame in enumerate(ctx.timeline["info"]["frames"]):
        pfs = frame["participantFrames"]
        row = {"minute": i, "self": _cs(pfs.get(str(me["participantId"]), {}))}
        if opp is not None:
            row["opponent"] = _cs(pfs.get(str(opp["participantId"]), {}))
        rows.append(row)
    return rows
