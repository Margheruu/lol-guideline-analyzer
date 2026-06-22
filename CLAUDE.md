# CLAUDE.md — LoL Guideline-Adherence Analyzer (Project)

Global rules in `~/.claude/CLAUDE.md` also apply (Japanese conversation,
English files, ask before acting, senior-DS persona). This file adds
project-specific specs. Keep it updated as the project evolves.

## Goal
Evaluate whether a player followed their **own predefined guidelines** in
League of Legends matches, identify where they deviated, and **visualize**
the deviations. Guidelines are user-authored, measurable rules.

## Scope — v1
- Data source: **official Riot Games API only** (no scraping, no replay
  parsing, no video/GPU).
- Granularity: post-game stats + **timeline at 60s frames** and discrete
  events (kills, item purchases, wards, etc.).
- Deliverable: ingest matches -> evaluate rule adherence -> visualize.

Deferred to later phases:
- Phase 2: second-level data (health/mana over time, summoner-spell usage)
  via replay `.rofl` playback + Live Client Data API (local port 2999).
- Phase 3 (only if needed): computer-vision on replay video (GPU / RTX 3060,
  torchvision/opencv/ultralytics). Add packages then, not before.

## Data Source — Riot API
Get a free dev key at developer.riotgames.com. **Never commit the key**;
read it from env var `RIOT_API_KEY`.

Routing:
- `account-v1` / `match-v5`: regional routing — `asia` / `americas` /
  `europe` (use `asia` for KR/JP players).
- `summoner-v4` etc.: platform routing — `jp1`, `na1`, `kr`, ...

Core endpoints (verify against current docs before coding):
- `GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}` -> `puuid`
- `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` -> match id list
- `GET /lol/match/v5/matches/{matchId}` -> full post-game detail
- `GET /lol/match/v5/matches/{matchId}/timeline` -> per-frame + events

Rate limits (dev key, typical): ~20 req/s and ~100 req/2min. Respect
`Retry-After`; back off with `tenacity`. Cache raw responses to disk to avoid
refetching (timeline is immutable per match).

### What the timeline provides (v1-usable)
- `participantFrames` every 60s: `position{x,y}`, `currentGold`/`totalGold`,
  `level`, `xp`, `minionsKilled`, `jungleMinionsKilled`, `championStats`
  (health/healthMax/power/etc. — **sampled at the frame, not continuous**),
  `damageStats`.
- `events` with timestamps: `CHAMPION_KILL` (**with position x,y**, killer/
  victim/assist), `ITEM_PURCHASED`/`SOLD`/`DESTROYED`, `WARD_PLACED`/`KILL`,
  `SKILL_LEVEL_UP`, `LEVEL_UP`, `BUILDING_KILL`, `ELITE_MONSTER_KILL`, ...

### Not available from the API (do NOT promise in v1)
- Continuous (second-level) health/mana between frames.
- Summoner-spell cast timing / cooldown usage.
- Ability cast timing, exact movement between frames.

## Guideline Evaluation Model
Treat each guideline as a **measurable rule** over timeline data; output a
per-rule verdict plus the evidence (timestamp, location, value vs target).

Rule examples (illustrative — final set is user-defined):
- CS target: `minionsKilled at 10:00 >= threshold`.
- Deaths before N minutes: count `CHAMPION_KILL` where victim = player.
- Recall discipline: back when `currentGold >= G` and not mid-objective.
- Vision: `WARD_PLACED` count per interval >= target.
- Death positioning: classify kill/death `position` into map zones; flag
  deaths in high-risk zones.
- Objective participation: player near `ELITE_MONSTER_KILL` position/time.

Design notes:
- Implement rules as small, pure, **testable** functions over a normalized
  event/frame schema — not ad hoc code per match.
- Each rule returns: `passed: bool`, `score`, `evidence[]`, `message`.
- Keep guideline definitions in a **config (YAML/JSON)**, not hard-coded, so
  the user can edit their own guidelines without code changes.
- Be explicit about uncertainty from 60s sampling (e.g. gold/health are
  frame-sampled, so timing-based rules have ~1-min resolution).

## Visualization
- Map-based: plot kill/death positions on the Summoner's Rift map (Riot Data
  Dragon provides the map image + champion/item assets).
- Timeline: gold/xp/CS diff vs time, with rule pass/fail markers.
- Per-match scorecard: rules passed/failed with evidence links.
- Interactive review via **Streamlit** (or Dash); static charts for reports.
- Use Data Dragon (ddragon) for champion/item/spell names, icons, map image;
  pin the patch/version used.

## Suggested Structure
```
src/
  ingest/     # Riot API client, rate-limit, caching, raw->normalized schema
  rules/      # one module per rule + a registry; loads guideline config
  eval/       # run rules over a match, aggregate verdicts
  viz/        # map plots, timeline charts, scorecards
  app/        # Streamlit entry point
config/        # guideline definitions (YAML/JSON)
data/raw/      # cached API responses (gitignored)
data/derived/  # normalized tables (gitignored)
notebooks/     # EDA only; reusable logic moves into src/
tests/         # unit tests for rules (fixtures from sample timelines)
```

## Constraints / Reminders
- ToS: use the official API; do not scrape OP.GG/U.GG etc. Production key
  required before public release.
- Multi-user: usable by the author plus a small private group of players.
  **Each analyzed player must opt in by providing their own Riot ID** — never
  query someone's account without consent. Store others' data locally only;
  do not redistribute or sell it.
- Secrets: `RIOT_API_KEY` via env; add `.env` and `data/` to `.gitignore`.
- Validation: build rules with **unit tests** on saved sample timelines so
  evaluation logic is reproducible and regression-safe.
- Env: conda env `ds-claude` (see `environment.yml`); `conda activate` it
  before running anything.
