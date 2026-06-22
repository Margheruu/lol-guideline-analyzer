"""Render a kill/death map for a player's most recent match."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.runner import participant_id_for  # noqa: E402
from src.ingest.riot_client import RiotClient  # noqa: E402
from src.rules.base import MatchContext  # noqa: E402
from src.viz.map_plot import save_combat_map  # noqa: E402

riot_id = sys.argv[1] if len(sys.argv) > 1 else "Bammmoo#ztmy"
region = sys.argv[2] if len(sys.argv) > 2 else "asia"
game_name, tag_line = riot_id.split("#", 1)

with RiotClient(region=region) as client:
    puuid = client.puuid_by_riot_id(game_name, tag_line)
    match_id = client.match_ids(puuid, count=1)[0]
    match = client.match(match_id)
    timeline = client.timeline(match_id)

ctx = MatchContext(match_id, puuid, participant_id_for(match, puuid), match, timeline)
out = save_combat_map(
    ctx, Path(__file__).resolve().parents[1] / "data" / "derived" / f"{match_id}_combat.png"
)
print("saved", out)
