# LoL Guideline-Adherence Analyzer

Evaluate whether a player followed their own predefined guidelines in League
of Legends matches, surface where they deviated, and visualize it.

See `CLAUDE.md` for the full spec, data sources, and roadmap.

## Setup
```powershell
# 1. Create & activate the conda env
conda env create -f environment.yml
conda activate ds-claude

# 2. (Optional, later) GPU PyTorch for Phase 3 video work
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# 3. Set your Riot API key (get a dev key at developer.riotgames.com)
$env:RIOT_API_KEY = "RGAPI-xxxxxxxx"   # or put it in a .env file (gitignored)
```

## Layout
- `src/ingest/` — Riot API client (routing, rate-limit backoff, disk cache)
- `src/rules/`  — one rule per guideline + registry; config-driven
- `src/eval/`   — run rules over a match, aggregate verdicts
- `src/viz/`    — map plots, timeline charts, scorecards
- `src/app/`    — Streamlit entry point
- `config/`     — user-authored `guidelines.yaml`
- `data/`       — cached API responses & derived tables (gitignored)
- `tests/`      — unit tests for rules (fixtures from sample timelines)

## v1 scope
Official Riot API only (post-game stats + 60s timeline frames + events).
No scraping, no replay parsing, no video/GPU. See `CLAUDE.md`.
