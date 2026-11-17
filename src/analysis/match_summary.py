"""One-line, human-readable labels for the match picker."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

JST = timezone(timedelta(hours=9))

# Only queues we are sure about; anything else falls back to the game mode.
QUEUE_NAMES = {
    400: "ノーマル",
    420: "ランク（ソロ/デュオ）",
    430: "ノーマル（ブラインド）",
    440: "ランク（フレックス）",
    450: "ARAM",
    490: "クイックプレイ",
}
ROLE_SHORT = {"TOP": "TOP", "JUNGLE": "JG", "MIDDLE": "MID", "BOTTOM": "ADC", "UTILITY": "SUP"}


def match_label(match: dict[str, Any], puuid: str, champ_names: dict[str, str] | None = None) -> str:
    """e.g. '11/16 23:53｜ノーマル｜フェイ（MID）｜敗北' (time in JST).

    ``champ_names`` maps Riot championName ids to display names; the id is
    shown when a name is missing.
    """
    info = match["info"]
    when = datetime.fromtimestamp(info["gameCreation"] / 1000, JST).strftime("%m/%d %H:%M")
    queue = QUEUE_NAMES.get(info.get("queueId"), f"その他（{info.get('gameMode', '?')}）")
    me = next((p for p in info["participants"] if p.get("puuid") == puuid), None)
    if me is None:
        return f"{when}｜{queue}"
    champ = (champ_names or {}).get(me["championName"], me["championName"])
    role = ROLE_SHORT.get(me.get("teamPosition") or "")
    result = "勝利" if me.get("win") else "敗北"
    return "｜".join([when, queue, champ + (f"（{role}）" if role else ""), result])
