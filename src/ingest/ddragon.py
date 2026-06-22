"""Data Dragon helpers: fetch & cache static assets (map image, version).

Official CDN, version-pinned. Assets are cached under `assets/` (gitignored).
"""
from __future__ import annotations

from pathlib import Path

import httpx

ASSETS = Path(__file__).resolve().parents[2] / "assets"
_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"


def latest_version() -> str:
    """Latest Data Dragon version string (cached locally)."""
    ASSETS.mkdir(exist_ok=True)
    cache = ASSETS / "version.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8").strip()
    version = httpx.get(_VERSIONS_URL, timeout=15).json()[0]
    cache.write_text(version, encoding="utf-8")
    return version


def sr_map_image() -> Path:
    """Path to the Summoner's Rift minimap (map11.png), downloading if needed."""
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / "map11.png"
    if not path.exists():
        version = latest_version()
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/map/map11.png"
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        path.write_bytes(resp.content)
    return path
