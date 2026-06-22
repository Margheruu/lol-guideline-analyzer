"""Data Dragon helpers: fetch & cache static assets (map image, version).

Official CDN, version-pinned. Assets are cached under `assets/` (gitignored).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def item_data(locale: str = "ja_JP") -> dict[str, Any]:
    """Item metadata keyed by item id (name, gold, into, tags, maps)."""
    ASSETS.mkdir(exist_ok=True)
    cache = ASSETS / f"item_{locale}.json"
    if not cache.exists():
        version = latest_version()
        url = (f"https://ddragon.leagueoflegends.com/cdn/{version}"
               f"/data/{locale}/item.json")
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        cache.write_text(resp.text, encoding="utf-8")
    return json.loads(cache.read_text(encoding="utf-8"))["data"]
