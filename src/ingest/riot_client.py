"""Riot Games API client: routing, rate-limit backoff, and disk caching.

Reads the API key from the ``RIOT_API_KEY`` environment variable. Raw match
and timeline responses are cached under ``data/raw/`` because they are
immutable once a match is finished.

NOTE: This is a v1 skeleton. Verify endpoint paths and rate limits against the
current Riot API docs before relying on it in production.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Regional routing host for account-v1 / match-v5.
REGIONAL = {"asia", "americas", "europe"}

# data/raw relative to the project root (this file: src/ingest/riot_client.py).
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


class RiotClient:
    """Thin client over the endpoints needed for v1 (account + match-v5)."""

    def __init__(self, region: str = "asia", api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("RIOT_API_KEY")
        if not self.api_key:
            raise RuntimeError("RIOT_API_KEY is not set.")
        if region not in REGIONAL:
            raise ValueError(f"region must be one of {sorted(REGIONAL)}")
        self.region = region
        self._client = httpx.Client(
            base_url=f"https://{region}.api.riotgames.com",
            headers={"X-Riot-Token": self.api_key},
            timeout=15.0,
        )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # --- low-level GET with retry on 429 / 5xx ---
    # TODO: honor the `Retry-After` header explicitly for 429 responses.
    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = self._client.get(path, params=params)
        resp.raise_for_status()  # 429 / 5xx -> retry; 4xx -> raise
        return resp.json()

    def _cached(self, key: str, fetch: Callable[[], Any]) -> Any:
        f = CACHE_DIR / f"{key}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
        data = fetch()
        f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    # --- endpoints ---
    def puuid_by_riot_id(self, game_name: str, tag_line: str) -> str:
        """Resolve a Riot ID (gameName#tagLine) to a PUUID."""
        data = self._get(
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        return data["puuid"]

    def match_ids(self, puuid: str, count: int = 20, start: int = 0) -> list[str]:
        """Return recent match ids for a PUUID (newest first)."""
        return self._get(
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids",
            params={"start": start, "count": count},
        )

    def match(self, match_id: str) -> dict[str, Any]:
        """Full post-game detail (cached)."""
        return self._cached(
            f"match_{match_id}", lambda: self._get(f"/lol/match/v5/matches/{match_id}")
        )

    def timeline(self, match_id: str) -> dict[str, Any]:
        """Per-frame (60s) + event timeline (cached)."""
        return self._cached(
            f"timeline_{match_id}",
            lambda: self._get(f"/lol/match/v5/matches/{match_id}/timeline"),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "RiotClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
