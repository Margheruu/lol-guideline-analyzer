"""Role keys, display labels, and guideline-file mapping.

Single source of truth for both src/app/streamlit_app.py and
scripts/smoke_fetch.py, so they don't each grow their own copy of this
mapping.
"""
from __future__ import annotations

ROLE_KEYS = ["top", "jungle", "mid", "adc", "support"]

ROLE_LABELS = {
    "top": "トップ",
    "jungle": "ジャングル",
    "mid": "ミッド",
    "adc": "ADC",
    "support": "サポート",
}

# Riot's match-v5 `teamPosition` values -> our role keys.
TEAM_POSITION_TO_ROLE = {
    "TOP": "top",
    "JUNGLE": "jungle",
    "MIDDLE": "mid",
    "BOTTOM": "adc",
    "UTILITY": "support",
}


def guidelines_filename(role_key: str) -> str:
    """The config/ filename for a role key, e.g. "adc" -> "guidelines_adc.yaml"."""
    return f"guidelines_{role_key}.yaml"


def role_for_team_position(team_position: str | None) -> str:
    """Map a match's teamPosition to a role key, defaulting to the first
    role when unknown (e.g. ARAM/Arena matches report an empty string).
    """
    return TEAM_POSITION_TO_ROLE.get(team_position or "", ROLE_KEYS[0])
