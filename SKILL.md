---
name: lol-guideline-adherence-analyzer
description: Evaluate whether a League of Legends player followed their own predefined guidelines (CS targets, deaths, recall timing, vision, itemization, objective participation) using official Riot API match/timeline data, and visualize the deviations. Use when the user wants to add/edit a guideline rule, ingest and evaluate a match against config/guidelines.yaml, debug a rule verdict, or run/extend this project's Streamlit review app.
---

# LoL Guideline-Adherence Analyzer

Full project spec, data model, and design decisions live in `CLAUDE.md` —
read it first; this file is the task-oriented "how do I..." guide.

## Orientation
- `src/ingest/riot_client.py` — Riot API client (regional/platform routing,
  rate-limit backoff via `tenacity`, disk cache under `data/raw/`)
- `src/rules/` — one module per guideline rule + `registry.py`; rules are
  registered with `@register("<rule_id>")` and are pure functions
  `(MatchContext, params: dict) -> RuleResult` (see `src/rules/base.py`)
- `src/eval/runner.py` — loads `config/guidelines.yaml`, runs each enabled
  rule, returns the list of `RuleResult` verdicts
- `src/viz/` — Pillow-based map/timeline rendering (**not matplotlib** — its
  Agg renderer crashes in the `ds-claude` env)
- `src/app/streamlit_app.py` — Streamlit review UI
- `config/guidelines.yaml` — user-authored rule config (id, params, enabled,
  Japanese `label:`)
- `data/raw/` — cached Riot API responses (gitignored, immutable per match)
- `tests/` — unit tests per rule, fixtures from saved sample timelines
- `ROADMAP.md` — master ledger of every guideline rule: PDF source, signal,
  and status (✅ implemented / 🔜 planned / 🟡 noisy / ⛔ out of scope)

## Common tasks

### Add or change a guideline rule
1. Check `ROADMAP.md` for the rule's intended spec (source guideline, data
   signal, known caveats) before writing code — don't invent a new rule
   that isn't on the ledger without asking the user first.
2. Implement it as a pure function in `src/rules/<name>.py`, decorated
   `@register("<rule_id>")`. No I/O inside a rule — everything it needs is
   already on `MatchContext` (`match`, `timeline`, `participant_id`, `puuid`).
3. Return a `RuleResult(rule_id, passed, score, message, evidence=[...])`;
   `message` is **Japanese** (shown to the user), `rule_id` stays English.
4. Add a unit test in `tests/` against a saved fixture in `data/raw/`
   (e.g. `match_JP1_589071001.json` / `timeline_JP1_589071001.json`).
5. Register it in `config/guidelines.yaml` with `id`, `params`, and a
   Japanese `label:`.
6. Flip its `ROADMAP.md` status (🔜 → ✅) in the same change.

### Ingest and evaluate a match
- Never query a Riot ID without that player's consent (multi-user opt-in
  rule in `CLAUDE.md`).
- `python scripts/smoke_fetch.py "Name#TAG" --region asia` — fetch, cache,
  evaluate, print a death report (fast sanity check for a single match).
- `python scripts/plot_match.py "Name#TAG" asia` — render the kill/death map
  to `data/derived/`.
- `python scripts/inspect_itemization.py ...` — inspect item-purchase timing
  for the core-item-timing rule.
- `streamlit run src/app/streamlit_app.py` — full interactive review (rule
  verdicts, death report, kill/death map).
- Activate the `ds-claude` conda env before running any of the above.

### Update the shared Riot API key (daily — dev keys expire after 24h)
1. developer.riotgames.com → "Regenerate API Key" → copy the new key.
2. `conda activate ds-claude`, then `python scripts/update_api_key.py` and
   paste the key when prompted. This rewrites the local `.env` and copies a
   ready-to-paste `RIOT_API_KEY = "..."` TOML line to the clipboard.
3. Paste that into the deployed app's Secrets (share.streamlit.io → the app
   → ⋮ → Settings → Secrets) → Save → **Reboot app**. This is the
   persistent source of truth for every visitor — always do this step.

Quick alternative when you're away from this repo (e.g. on a phone): open
the app → sidebar → "🔧 管理者用" → enter `ADMIN_PASSWORD` → paste the new
key. Applies instantly, no reboot needed — but it only patches the *running*
process, so it does **not** survive the next restart (Cloud sleep/wake,
redeploy, maintenance). Still do step 3 above once you're back at a PC.

### Debugging a rule verdict
- Rules only see 60s-sampled frames + discrete events — resist adding
  sub-minute precision claims; if a verdict looks wrong, check whether it's
  a genuine bug vs. an expected frame-sampling artifact (note it in the
  rule's `message`/evidence rather than silently tightening the check).
- Reuse the cached fixtures in `data/raw/` instead of refetching from the
  live API while iterating.

## Constraints to respect
- Official Riot API only for v1 — no scraping, no replay parsing, no GPU/CV
  (that's Phase 2/3, deliberately deferred; don't pull those in early).
- `RIOT_API_KEY` from env/`.env` only — never hard-code or commit it.
- User-facing text (Streamlit labels, rule `message`, `label` in
  `guidelines.yaml`) is Japanese; code, identifiers, rule `id`s, file names,
  and commits stay English.
