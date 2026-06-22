# CLAUDE.md — LoL Guideline-Adherence Analyzer (Project)

Global rules in `~/.claude/CLAUDE.md` also apply (Japanese conversation,
English files, ask before acting, senior-DS persona). This file adds
project-specific specs. Keep it updated as the project evolves.

**App UI language**: the Streamlit app's *display text* is **Japanese** (the
user's language). Code, comments, identifiers, file names, commits, and rule
`message` strings stay **English**. (Localizing rule messages is a possible
follow-up.)

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
Verified against real data (match JP1_589071001, 26 frames @ 60s interval).
- `participantFrames` every 60s: `position{x,y}`, `currentGold`/`totalGold`,
  `goldPerSecond`, `level`, `xp`, `minionsKilled`, `jungleMinionsKilled`,
  `timeEnemySpentControlled`, `damageStats`, and `championStats` — which DOES
  include `health`/`healthMax` and `power`/`powerMax` (mana), plus armor, AD,
  AP, etc. So health/mana ARE available, but **sampled per 60s frame**.
- `events` with timestamps: `CHAMPION_KILL`, `CHAMPION_SPECIAL_KILL`,
  `ITEM_PURCHASED`/`SOLD`/`DESTROYED`/`UNDO`, `WARD_PLACED`/`WARD_KILL`,
  `SKILL_LEVEL_UP`, `LEVEL_UP`, `BUILDING_KILL`, `TURRET_PLATE_DESTROYED`,
  `ELITE_MONSTER_KILL`, `DRAGON_SOUL_GIVEN`, `OBJECTIVE_BOUNTY_*`.
- `CHAMPION_KILL` is rich: `position{x,y}`, `killerId`/`victimId`, `bounty`,
  `killStreakLength`, and `victimDamageDealt`/`victimDamageReceived` arrays
  giving the per-spell damage breakdown (incl. summoner spells like
  `summonerdot` = Ignite) around the kill.

### Not available from the API (do NOT promise in v1)
- Continuous (sub-minute) health/mana — only the 60s frame samples exist.
- A complete summoner-spell cast/cooldown log. (Usage in a fight is partially
  inferable from the `CHAMPION_KILL` damage arrays, but not a full history.)
- A clean ability-cast event stream; exact movement between 60s frames.

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

### v1 guideline decisions (from the user's ADC guidelines)
- **Champion-specific** guidelines (e.g. Caitlyn/Kai'Sa combos, builds) are
  **out of scope for v1** — only role-general, measurable rules.
- **Recall**: primarily wave-state driven (theory). Secondary bonus signal:
  recall is well-timed when **enemy JG is bot-side AND ally JG is top-side**.
- **Boots / defensive items**: theory-based (match enemy damage type). Going
  defensive is for when the player can't keep trading in skirmishes/fights —
  that judgment is hard to measure, so v1 only checks **boot-type correctness
  when a defensive boot was built** and reports the damage profile as info.
- **Jungle-invade cover**: follow theory — ADC generally does NOT abandon
  lane for early jungle skirmishes (low reward, high risk).
- **Snowball** = lane lead **plus** objective-fight participation.
- Measurable damage-type signal: prefer the player's **actual damage taken**
  split (physical/magic) over guessing from enemy champion identity. Enemy CC
  amount (`totalTimeCCDealt`) is **low-confidence** (unit unclear) — avoid.

## Visualization
- **Rendered with Pillow, not matplotlib** — matplotlib's Agg renderer crashes
  natively in the `ds-claude` env (STATUS_STACK_BUFFER_OVERRUN). `src/viz/
  map_plot.py` draws on the map image with PIL and returns a PIL Image.
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
