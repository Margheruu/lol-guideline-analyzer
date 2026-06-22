"""Streamlit entry point (v1 skeleton).

Run with:  streamlit run src/app/streamlit_app.py

This is a placeholder wiring: enter a Riot ID, pick a match, evaluate the
configured guidelines, and show the verdicts. Visualization (map plots,
timeline charts) is added in src/viz/ and rendered here.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.eval.runner import evaluate, load_guidelines, participant_id_for
from src.ingest.riot_client import RiotClient
from src.rules.base import MatchContext

GUIDELINES = Path(__file__).resolve().parents[2] / "config" / "guidelines.yaml"


def main() -> None:
    st.set_page_config(page_title="LoL Guideline Analyzer", layout="wide")
    st.title("LoL Guideline-Adherence Analyzer")

    region = st.selectbox("Routing region", ["asia", "americas", "europe"])
    riot_id = st.text_input("Riot ID (gameName#tagLine)", "")

    if not st.button("Analyze") or "#" not in riot_id:
        st.info("Enter a Riot ID like Name#TAG and click Analyze.")
        return

    game_name, tag_line = riot_id.split("#", 1)
    with RiotClient(region=region) as client:
        puuid = client.puuid_by_riot_id(game_name, tag_line)
        match_id = client.match_ids(puuid, count=1)[0]
        match = client.match(match_id)
        timeline = client.timeline(match_id)

    ctx = MatchContext(
        match_id=match_id,
        puuid=puuid,
        participant_id=participant_id_for(match, puuid),
        match=match,
        timeline=timeline,
    )
    results = evaluate(ctx, load_guidelines(GUIDELINES))

    st.subheader(f"Match {match_id}")
    for r in results:
        icon = "✅" if r.passed else "❌"
        st.write(f"{icon} **{r.rule_id}** — {r.message}")
    # TODO: render map (kill/death positions) and timeline charts from src/viz.


if __name__ == "__main__":
    main()
