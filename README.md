# LoL Guideline-Adherence Analyzer

Evaluate whether a player followed their own predefined guidelines in League
of Legends matches, surface where they deviated, and visualize it.

See `CLAUDE.md` for the full spec, data sources, and roadmap.

## Setup

**Option A — full conda env** (notebooks, ML experimentation):
```powershell
conda env create -f environment.yml
conda activate ds-claude

# (Optional, later) GPU PyTorch for Phase 3 video work
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

**Option B — lightweight venv** (just running the app on a new device):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-app.txt
```

Then, either way, set your Riot API key (get a dev key at developer.riotgames.com):
```powershell
$env:RIOT_API_KEY = "RGAPI-xxxxxxxx"   # or put it in a .env file (gitignored)
```

## Run the app
```powershell
streamlit run src/app/streamlit_app.py
```
Enter a Riot ID (e.g. `Name#TAG`), pick a recent match, and see the guideline
verdicts, a death report, and a kill/death map.

Other entry points:
- `python scripts/smoke_fetch.py "Name#TAG" --region asia` — fetch + evaluate + death report
- `python scripts/plot_match.py "Name#TAG" asia` — render the kill/death map to `data/derived/`

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
