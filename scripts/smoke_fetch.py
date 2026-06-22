"""Smoke test: fetch one real match via the Riot API and inspect its schema.

Usage (env RIOT_API_KEY or .env must be set):
    python scripts/smoke_fetch.py "Bammmoo#ztmy" --region asia

Verifies the key works end-to-end (account -> match ids -> match + timeline)
and prints a compact schema summary so we can confirm which fields the
guideline rules can rely on.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter

# Allow running as a script: add project root to sys.path.
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from pathlib import Path  # noqa: E402

from src.eval.runner import evaluate, load_guidelines, participant_id_for  # noqa: E402
from src.ingest.riot_client import RiotClient  # noqa: E402
from src.rules.base import MatchContext  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("riot_id", help="gameName#tagLine, e.g. Bammmoo#ztmy")
    ap.add_argument("--region", default="asia", choices=["asia", "americas", "europe"])
    args = ap.parse_args()

    game_name, tag_line = args.riot_id.split("#", 1)
    with RiotClient(region=args.region) as client:
        puuid = client.puuid_by_riot_id(game_name, tag_line)
        print(f"puuid: {puuid[:16]}... (len {len(puuid)})")

        match_ids = client.match_ids(puuid, count=5)
        print(f"recent match ids: {match_ids}")
        if not match_ids:
            print("No matches found.")
            return

        match_id = match_ids[0]
        match = client.match(match_id)
        timeline = client.timeline(match_id)

        frames = timeline["info"]["frames"]
        print(f"\n=== {match_id} ===")
        print(f"frames: {len(frames)}  (interval ~{timeline['info'].get('frameInterval')} ms)")

        pf = frames[min(10, len(frames) - 1)]["participantFrames"]["1"]
        print(f"participantFrame[1] keys: {sorted(pf.keys())}")
        if "championStats" in pf:
            print(f"  championStats keys: {sorted(pf['championStats'].keys())}")

        event_types = Counter(
            ev["type"] for f in frames for ev in f.get("events", [])
        )
        print(f"event types: {dict(event_types)}")

        kill = next(
            (ev for f in frames for ev in f.get("events", [])
             if ev.get("type") == "CHAMPION_KILL"),
            None,
        )
        print(f"sample CHAMPION_KILL pos/time: "
              f"{kill.get('position')} @ {kill.get('timestamp')}ms" if kill else "none")

        # --- end-to-end: evaluate the configured guidelines on this match ---
        ctx = MatchContext(
            match_id=match_id,
            puuid=puuid,
            participant_id=participant_id_for(match, puuid),
            match=match,
            timeline=timeline,
        )
        guidelines = load_guidelines(Path(__file__).resolve().parents[1] / "config" / "guidelines.yaml")
        print("\n=== guideline evaluation ===")
        for r in evaluate(ctx, guidelines):
            print(f"{'PASS' if r.passed else 'FAIL'}  {r.rule_id}: {r.message}")


if __name__ == "__main__":
    main()
