"""Feasibility check: can we evaluate boot/defensive-item choice and 15-min
lane state from Riot data? Inspect a cached match for the needed fields."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MATCH_ID = sys.argv[1] if len(sys.argv) > 1 else "JP1_589071001"
NAME = (sys.argv[2] if len(sys.argv) > 2 else "Bammmoo").lower()

match = json.loads((RAW / f"match_{MATCH_ID}.json").read_text(encoding="utf-8"))
timeline = json.loads((RAW / f"timeline_{MATCH_ID}.json").read_text(encoding="utf-8"))
parts = match["info"]["participants"]


def name_of(p: dict) -> str:
    return (p.get("riotIdGameName") or p.get("summonerName") or "").lower()


me = next(p for p in parts if name_of(p) == NAME)
print(f"me: {me['championName']} pos={me.get('teamPosition')} team={me['teamId']}")
print(f"items: {[me[f'item{i}'] for i in range(7)]}")
print(f"my dmg DEALT  P/M/T: {me['physicalDamageDealtToChampions']}/"
      f"{me['magicDamageDealtToChampions']}/{me['trueDamageDealtToChampions']}")
print(f"my dmg TAKEN  P/M/T: {me['physicalDamageTaken']}/"
      f"{me['magicDamageTaken']}/{me['trueDamageTaken']}")

enemy = [p for p in parts if p["teamId"] != me["teamId"]]
ep = sum(p["physicalDamageDealtToChampions"] for p in enemy)
em = sum(p["magicDamageDealtToChampions"] for p in enemy)
et = sum(p["trueDamageDealtToChampions"] for p in enemy)
tot = ep + em + et or 1
print(f"\nENEMY team dmg dealt to champs: "
      f"phys {ep/tot:.0%} / magic {em/tot:.0%} / true {et/tot:.0%}")
print("enemy CC time (totalTimeCCDealt s): "
      + ", ".join(f"{p['championName']}={p.get('totalTimeCCDealt')}" for p in enemy))

# what damage type the PLAYER actually took (ideal signal for resist choice)
pt, mt, tt = me["physicalDamageTaken"], me["magicDamageTaken"], me["trueDamageTaken"]
tk = pt + mt + tt or 1
print(f"my dmg TAKEN split: phys {pt/tk:.0%} / magic {mt/tk:.0%} / true {tt/tk:.0%}")

# 15-min lane state vs same-position opponent
opp = next(p for p in enemy if p.get("teamPosition") == me.get("teamPosition"))
frames = timeline["info"]["frames"]
f15 = frames[15] if len(frames) > 15 else frames[-1]


def cs(pf: dict) -> int:
    return pf["minionsKilled"] + pf["jungleMinionsKilled"]


mpf = f15["participantFrames"][str(me["participantId"])]
opf = f15["participantFrames"][str(opp["participantId"])]
print(f"\nlane opponent: {opp['championName']}")
print(f"@~15min  CS {cs(mpf)} vs {cs(opf)} (diff {cs(mpf)-cs(opf):+d})")
print(f"@~15min  gold {mpf['totalGold']} vs {opf['totalGold']} "
      f"(diff {mpf['totalGold']-opf['totalGold']:+d})")
print(f"@~15min  level {mpf['level']} vs {opf['level']}")
