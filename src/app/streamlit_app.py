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
    # NOTE: UI display text is Japanese (the user's language); code/comments
    # stay English. See CLAUDE.md.
    st.set_page_config(page_title="LoL ガイドライン分析", layout="wide")
    st.title("LoL ガイドライン適合度アナライザー")

    with st.sidebar:
        region = st.selectbox("リージョン（ルーティング）",
                              ["asia", "americas", "europe"])
        riot_id = st.text_input("Riot ID（ゲーム名#タグ）", "Bammmoo#ztmy")
        count = st.slider("表示する試合数", 1, 20, 5)

    if "#" not in riot_id:
        st.info("サイドバーに Riot ID（例: 名前#TAG）を入力してください。")
        return

    game_name, tag_line = riot_id.split("#", 1)
    try:
        puuid = fetch_puuid(region, game_name, tag_line)
        match_ids = fetch_match_ids(region, puuid, count)
    except Exception as exc:  # noqa: BLE001 — surface API errors to the user
        st.error(f"Riot API リクエストに失敗しました: {exc}")
        return

    if not match_ids:
        st.warning("この Riot ID の試合が見つかりませんでした。")
        return

    match_id = st.selectbox("試合", match_ids)
    match, timeline = fetch_match(region, match_id)
    ctx = MatchContext(match_id, puuid,
                       participant_id_for(match, puuid), match, timeline)
    me = match["info"]["participants"][ctx.participant_id - 1]

    kda = f"{me.get('kills')}/{me.get('deaths')}/{me.get('assists')}"
    outcome = "勝利" if me.get("win") else "敗北"
    st.subheader(f"{me.get('championName')} · {me.get('teamPosition')} · "
                 f"KDA {kda} · {outcome}")

    left, right = st.columns(2)
    with left:
        st.markdown("### ガイドライン判定")
        for r in evaluate(ctx, load_guidelines(GUIDELINES)):
            st.markdown(f"{'✅' if r.passed else '❌'} **{r.rule_id}** — {r.message}")
            for ev in r.evidence[:5]:
                when = f" @ {ev.timestamp_ms // 60000}分" if ev.timestamp_ms else ""
                st.caption(f"• {ev.detail}{when}")
    with right:
        st.markdown("### キル / デス マップ")
        st.image(render_combat_map(ctx), use_container_width=True)
        st.caption("赤 ✕ = デス（○ = 最前列）、緑 = キル、金 = アシスト")

    st.markdown("### デスレポート")
    deaths = deaths_for(ctx)
    if not deaths:
        st.success("この試合はデスなし 🎉")
        return
    df = pd.DataFrame([{
        "分": d.timestamp_ms // 60000,
        "x": d.position.get("x"),
        "y": d.position.get("y"),
        "直前HP%": None if d.health_pct_before is None
        else round(d.health_pct_before * 100),
        "加害者": d.killer_champion,
        "主因ダメージ": d.top_damage_source,
        "周囲の味方数": d.allies_nearby,
        "最前列": d.is_frontmost,
    } for d in deaths])
    st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
