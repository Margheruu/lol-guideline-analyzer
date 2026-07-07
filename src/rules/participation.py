"""Team-fight participation rules."""
from __future__ import annotations

from typing import Any

from .base import Evidence, MatchContext, RuleResult
from .registry import register


def _me(ctx: MatchContext) -> dict[str, Any]:
    return ctx.match["info"]["participants"][ctx.participant_id - 1]


def _team_kills(ctx: MatchContext, team_id: int) -> int:
    for t in ctx.match["info"].get("teams", []):
        if t.get("teamId") == team_id:
            return t.get("objectives", {}).get("champion", {}).get("kills", 0)
    return 0


@register("kill_participation")
def kill_participation(ctx: MatchContext, params: dict[str, Any]) -> RuleResult:
    """Pass if (kills + assists) / team kills meets a target participation rate.

    Uses Riot's precomputed ``challenges.killParticipation`` when present
    (post-game stat, most accurate); falls back to a manual ratio otherwise.
    """
    target = float(params.get("min_participation", 0.5))
    me = _me(ctx)

    kp = me.get("challenges", {}).get("killParticipation")
    if kp is None:
        team_kills = _team_kills(ctx, me.get("teamId"))
        kp = ((me.get("kills", 0) + me.get("assists", 0)) / team_kills
              if team_kills else 0.0)

    passed = kp >= target
    score = min(kp / target, 1.0) if target else 1.0
    msg = f"キル関与率 {kp:.0%}（目標 {target:.0%} 以上）。"
    return RuleResult("kill_participation", passed, score, msg, [Evidence(detail=msg)])
