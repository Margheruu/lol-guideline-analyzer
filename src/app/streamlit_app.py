"""Streamlit app: analyze a player's match against their guidelines.

Run with:  streamlit run src/app/streamlit_app.py

Enter a Riot ID, pick a recent match, and see the guideline verdicts, a death
report, and a kill/death map. Wires together the ingest, eval, analysis, and
viz layers — all of which are unit-tested / verified on real data.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `from src...` work when launched via `streamlit run` (which only puts
# the script's own dir on sys.path).
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from src.analysis.deaths import deaths_for  # noqa: E402
from src.eval.runner import evaluate, load_guidelines, participant_id_for  # noqa: E402
from src.ingest.riot_client import RiotClient  # noqa: E402
from src.rules.base import MatchContext  # noqa: E402
from src.viz.map_plot import render_combat_map  # noqa: E402

GUIDELINES = ROOT / "config" / "guidelines.yaml"


@st.cache_data(show_spinner=False)
def fetch_puuid(region: str, game_name: str, tag_line: str) -> str:
    with RiotClient(region=region) as client:
        return client.puuid_by_riot_id(game_name, tag_line)


@st.cache_data(show_spinner=False)
def fetch_match_ids(region: str, puuid: str, count: int) -> list[str]:
    with RiotClient(region=region) as client:
        return client.match_ids(puuid, count=count)


@st.cache_data(show_spinner=False)
def fetch_match(region: str, match_id: str) -> tuple[dict, dict]:
    with RiotClient(region=region) as client:
        return client.match(match_id), client.timeline(match_id)


def main() -> None:
    st.set_page_config(page_title="LoL Guideline Analyzer", layout="wide")
    st.title("LoL Guideline-Adherence Analyzer")

    with st.sidebar:
        region = st.selectbox("Routing region", ["asia", "americas", "europe"])
        riot_id = st.text_input("Riot ID (gameName#tagLine)", "Bammmoo#ztmy")
        count = st.slider("Matches to list", 1, 20, 5)

    if "#" not in riot_id:
        st.info("Enter a Riot ID like `Name#TAG` in the sidebar.")
        return

    game_name, tag_line = riot_id.split("#", 1)
    try:
        puuid = fetch_puuid(region, game_name, tag_line)
        match_ids = fetch_match_ids(region, puuid, count)
    except Exception as exc:  # noqa: BLE001 — surface API errors to the user
        st.error(f"Riot API request failed: {exc}")
        return

    if not match_ids:
        st.warning("No matches found for this Riot ID.")
        return

    match_id = st.selectbox("Match", match_ids)
    match, timeline = fetch_match(region, match_id)
    ctx = MatchContext(match_id, puuid,
                       participant_id_for(match, puuid), match, timeline)
    me = match["info"]["participants"][ctx.participant_id - 1]

    kda = f"{me.get('kills')}/{me.get('deaths')}/{me.get('assists')}"
    outcome = "WIN" if me.get("win") else "LOSS"
    st.subheader(f"{me.get('championName')} · {me.get('teamPosition')} · "
                 f"KDA {kda} · {outcome}")

    left, right = st.columns(2)
    with left:
        st.markdown("### Guideline evaluation")
        for r in evaluate(ctx, load_guidelines(GUIDELINES)):
            st.markdown(f"{'✅' if r.passed else '❌'} **{r.rule_id}** — {r.message}")
            for ev in r.evidence[:5]:
                when = f" @ {ev.timestamp_ms // 60000}'" if ev.timestamp_ms else ""
                st.caption(f"• {ev.detail}{when}")
    with right:
        st.markdown("### Kill / death map")
        st.image(render_combat_map(ctx), use_container_width=True)
        st.caption("red ✕ = death (○ = most-forward), green = kill, gold = assist")

    st.markdown("### Death report")
    deaths = deaths_for(ctx)
    if not deaths:
        st.success("No deaths this game. 🎉")
        return
    df = pd.DataFrame([{
        "min": d.timestamp_ms // 60000,
        "x": d.position.get("x"),
        "y": d.position.get("y"),
        "HP% before": None if d.health_pct_before is None
        else round(d.health_pct_before * 100),
        "killer": d.killer_champion,
        "top damage": d.top_damage_source,
        "allies near": d.allies_nearby,
        "frontmost": d.is_frontmost,
    } for d in deaths])
    st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
