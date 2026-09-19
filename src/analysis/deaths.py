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

from src.ingest.ddragon import champion_data

# Approx enemy nexus position by team id (Summoner's Rift ~ 0..15000).
_ENEMY_BASE = {100: (14400, 14400), 200: (1500, 1500)}

# victimDamageReceived[].name values that aren't a championName -- map
# objects and summoner spells aren't in any Data Dragon locale file, so
# these are hand-maintained (stable, rarely-changing internal ids).
_SOURCE_NAME_JA = {
    "SRU_OrderMinionMelee": "ミニオン（近接・青）",
    "SRU_OrderMinionRanged": "ミニオン（遠隔・青）",
    "SRU_OrderMinionSiege": "ミニオン（攻城・青）",
    "SRU_OrderMinionSuper": "ミニオン（スーパー・青）",
    "SRU_ChaosMinionMelee": "ミニオン（近接・赤）",
    "SRU_ChaosMinionRanged": "ミニオン（遠隔・赤）",
    "SRU_ChaosMinionSiege": "ミニオン（攻城・赤）",
    "SRU_ChaosMinionSuper": "ミニオン（スーパー・赤）",
    "SRU_Razorbeak": "レイザービーク",
    "SRU_RazorbeakMini": "レイザービーク（小）",
    "SRU_Murkwolf": "マークウルフ",
    "SRU_MurkwolfMini": "マークウルフ（小）",
    "SRU_Krug": "クラッグ",
    "SRU_KrugMini": "クラッグ（小）",
    "SRU_Gromp": "グロンプ",
    "SRU_Red": "レッドブランブルバック",
    "SRU_Blue": "ブルーセンチネル",
    "SRU_Dragon": "ドラゴン",
    "sru_dragon_fire": "インフェルナルドレイク",
    "sru_dragon_water": "オーシャンドレイク",
    "sru_dragon_earth": "マウンテンドレイク",
    "sru_dragon_air": "クラウドドレイク",
    "sru_dragon_hextech": "ヘクステックドレイク",
    "sru_dragon_chemtech": "ケミテックドレイク",
    "sru_dragon_elder": "エルダードラゴン",
    "SRU_Baron": "バロンナッシャー",
    "SRU_RiftHerald": "ヘラルド",
    "summonerdot": "イグナイト",
    "summonerexhaust": "エグゾースト",
    "summonerflash": "フラッシュ",
    "summonerhaste": "ゴースト",
    "summonerheal": "ヒール",
    "summonerbarrier": "バリア",
    "summonersmite": "スマイト",
    "summonercleanse": "クレンズ",
    "summonerteleport": "テレポート",
}


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


def _resolve_champion_meta(champion_meta: dict[str, Any] | None) -> dict[str, Any]:
    """Data Dragon champion metadata, falling back to {} (-> English names
    everywhere) if unreachable. Tests pass ``champion_meta={}`` explicitly
    to avoid a real network call.
    """
    if champion_meta is not None:
        return champion_meta
    try:
        return champion_data()
    except Exception:  # noqa: BLE001 — ddragon fetch may fail offline
        return {}


def _champion_names(
    match: dict[str, Any], champion_meta: dict[str, Any],
) -> dict[int, str | None]:
    """participantId -> localized champion name (English if not found)."""
    en_names = _by_id(match, "championName")
    return {pid: (champion_meta.get(name, {}).get("name", name) if name else None)
            for pid, name in en_names.items()}


def _nearest_frame(frames: list[dict], ts: int) -> dict:
    return frames[min(ts // 60_000, len(frames) - 1)]


def _translate_source(name: str, source_type: str,
                      champion_meta: dict[str, Any]) -> str:
    """A victimDamageReceived name -> Japanese display text.

    Checks the hand-maintained table first regardless of ``source_type`` --
    Riot's ``type`` for non-champion sources (minion/monster/summoner-spell)
    isn't consistently documented, and these internal ids never collide with
    a real championName, so this is robust either way. Falls back to Data
    Dragon (a champion) or the raw ``name`` if nothing matches.
    """
    if source_type == "TOWER":
        return "タワー"
    if name in _SOURCE_NAME_JA:
        return _SOURCE_NAME_JA[name]
    return champion_meta.get(name, {}).get("name", name)


def _top_source(damage_received: list[dict],
               champion_meta: dict[str, Any]) -> str | None:
    if not damage_received:
        return None
    agg: dict[str, int] = {}
    type_of: dict[str, str] = {}
    for d in damage_received:
        name = d.get("name", "?")
        type_of[name] = d.get("type", "")
        agg[name] = agg.get(name, 0) + (
            d.get("physicalDamage", 0) + d.get("magicDamage", 0)
            + d.get("trueDamage", 0)
        )
    if not agg:
        return None
    top_name = max(agg, key=agg.get)
    return _translate_source(top_name, type_of[top_name], champion_meta)


def deaths_for(
    ctx: Any, nearby_radius: int = 2000,
    champion_meta: dict[str, Any] | None = None,
) -> list[DeathRecord]:
    """Return a DeathRecord for each time the player was the kill victim."""
    pid = ctx.participant_id
    teams = _by_id(ctx.match, "teamId")
    meta = _resolve_champion_meta(champion_meta)
    champs = _champion_names(ctx.match, meta)
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
            top = _top_source(ev.get("victimDamageReceived") or [], meta)

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
