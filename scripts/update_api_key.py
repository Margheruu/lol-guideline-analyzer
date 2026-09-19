"""Propagate a freshly-regenerated RIOT_API_KEY to every place it's needed.

Usage:
    python scripts/update_api_key.py                 # prompts (hidden input)
    python scripts/update_api_key.py RGAPI-xxxx...    # or pass it directly

Does NOT touch developer.riotgames.com — you still regenerate the key
yourself in the browser (dev keys expire every 24h and Riot's portal has no
API for this). This script only removes the busywork *after* that: it
updates the local `.env` and copies a ready-to-paste Streamlit Cloud
secrets snippet to the clipboard, so you just paste it into the app's
Settings -> Secrets and reboot.
"""
from __future__ import annotations

import getpass
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def update_env_file(key: str) -> None:
    line = f"RIOT_API_KEY={key}"
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        lines = [l for l in lines if not l.startswith("RIOT_API_KEY=")]
        lines.append(line)
    else:
        lines = [line]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(["clip"], input=text, text=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def main() -> None:
    key = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("New RIOT_API_KEY: ")
    key = key.strip()
    if not key:
        print("No key entered, aborting.")
        return

    update_env_file(key)
    print(f"Updated {ENV_PATH}")

    secret_snippet = f'RIOT_API_KEY = "{key}"'
    if copy_to_clipboard(secret_snippet):
        print("Streamlit Cloud secrets snippet copied to clipboard - "
              "paste it into the app's Settings -> Secrets, then reboot.")
    else:
        print(f"Paste this into the app's Settings -> Secrets:\n{secret_snippet}")


if __name__ == "__main__":
    main()
