# Rule Mapping — Discord Lane Guides → Measurable Rules

Maps the lane know-how from the user's LoL Discord server onto rules this
project can evaluate with the official Riot API (match + 60s timeline). Status
legend matches `ROADMAP.md`.

## Source & provenance
- **Source:** step-up guide posted in the user's LoL Discord server by its
  owner (ふつぐ), posts dated 2024-08 – 2024-10. The same author publishes a
  public version as the note.com magazine "LoL初心者向けステップアップ講座"
  (https://note.com/futugu).
- **Local copy:** `docs/discord/*.md` (copied by the user; **gitignored —
  local only, never commit or deploy**). Images were not copied.
  This file only cites section numbers and paraphrases; it does not
  reproduce the source text.
- **Section refs:** `Common ⑯` = 全レーン共通 §16, `TOP ②` = TOPレーンの勝ちかた
  §2, likewise `JG`, `MID`, `SUP`, `ADC`.
- **Known gaps in the copy:** Common §1–7, §10, §11, §15 and the SUP ward
  section ("後述") are missing. Judged not to affect measurable rules.
- **Environment drift:** the guide predates major system changes (Void
  Grubs 8:00 single wave, Herald ~15:00, no Atakhan, turret plates persist
  past 14:00, auto-granted support item, role quests). See
  `docs/review_persona_expert.md` for the measured fact sheet; never take
  objective timings from the guide.
- **Audience caveat:** written for beginners; some bars may be deliberately
  lenient, and some numbers are patch-dependent (e.g. JG ③ says scuttle
  spawns at 3:30; patch 26.1 moved it to 2:55). Keep all timings as YAML params.
- **ADC:** the user's own PDF stays authoritative. Discord-derived ADC items
  below are *proposals only* and are not applied to `guidelines_adc.yaml`.

## A. Existing rules vs. the source

| # | Source claim | Current state | Proposal | Roles |
|---|---|---|---|---|
| A1 | Common ⑯: a level deficit of ≥1 vs. the lane opponent = lane lost | `not_behind_at_minute` passes a 1-level deficit (`lvl_d >= -1`) | **Applied** `max_level_deficit: 0` | TOP/JG/MID/SUP (ADC: proposal) |
| A2 | Common ⑯: 2 deaths in lane = lane lost; Common ⑬: laning phase = 0:00–14:00 | `deaths_in_lane_phase` not implemented (🔜) | **Implemented** `deaths_in_lane_phase`, `max_deaths: 1`, `through_minute: 14` | TOP/JG/MID/SUP (ADC: disabled proposal) |
| A3 | Common ⑯: opponent finished a core item first = lane lost | core-item timing is app-only (no verdict) | Promote to a rule | all |
| A4 | SUP ②: enchanter/mage supports are fragile; Common ⑱: never fight outnumbered | `isolated_deaths` SUP `max_deaths: 0` | Keep (consistent) | SUP |
| A5 | Common ⑧: 70→80→90 CS @10 **in the practice tool** | `cs_per_minute` | Keep — practice-tool target, not a live-game bar | — |
| A6 | (no numbers in source) | `kill_participation`, `wards_per_interval` targets | Keep | — |

## B. New rule candidates

| # | Source claim | Signal | Status | Roles |
|---|---|---|---|---|
| B1 | TOP ② / MID ② / ADC ④ "reason 6": recall when holding 1000 gold | lane-phase frames with `currentGold >= 1000` for N consecutive frames | 🟡 (confounded, see results) | TOP/MID (ADC: proposal) |
| B2 | JG ③: full clear first, then recall and buy an 800/900g component | `jungleMinionsKilled` at 4:00 ≥ 24; gold spent on first shop trip ≥ 800 | ✅ `jungle_first_clear` (exempt if kill/assist by 4:00) | JG |
| B3 | Common ㉕: everyone places one control ward per objective setup | `challenges.controlWardsPlaced` per 10 min ≥ SUP 2.0 / JG 1.0 / TOP·MID 0.5 | ✅ `control_ward_rate` | TOP/JG/MID/SUP (ADC: disabled proposal) |
| B4 | Common ㉕: recall at objective timer 1:30–1:00, hold the pit from 0:20 | spawn times (dragon 5:00, grubs 6:00, herald 14:00, baron 20:00; respawns from `ELITE_MONSTER_KILL`) × player distance to pit at the nearest frame | 🟡 (60s frames) | all |
| B5 | SUP ①: support item quest completion | World Atlas → final support item time vs. enemy SUP (`ITEM_*` events) | 🔜 (no target time in source — compare to opponent) | SUP |
| B6 | TOP ④ / MID ⑤: mid-game, don't fight past the side-lane midpoint without vision/allies | death position in enemy half of a side lane × no ally nearby, after 14:00 | 🟡 | TOP/MID |
| B7 | Common ⑯: once lane is lost, stop taking fights | deaths after the A1/A2/A3 "lane lost" condition is met | 🟡 | all |
| B8 | ADC ③: win the level-2 race (6 first-wave + 3 second-wave melee) | `LEVEL_UP` (level 2) timestamps vs. lane opponents — event-precise | 🔜 | SUP (ADC: proposal) |
| B9 | Common ⑬: turret plates = 125g each during laning | `challenges.turretPlatesTaken` | info only (lane guides also say recall > plates) | TOP/MID |

## C. Not measurable with the v1 API (⛔)
- Trading pattern (short/long), skill dodging, triangle rule, minimap
  frequency, pings, gank setup decisions, team-comp / formation, focus,
  carry "late entry", end-game calls.
- **Any ward-location rule** (control ward in the dragon pit, "mandatory"
  bush wards, baron-pit ward): `WARD_PLACED` events carry no position
  (verified on `timeline_JP1_589071001.json`).

## Pass-rate check (2026-11-17)

**Data:** cached matches in `data/raw/` — 57 matches; 7 games < 16 min
excluded → 50 Summoner's Rift games, all 10 participants evaluated
(population baseline: same games, same rank bracket) = 100 player-games per
role. The focal player appears in 49 games (ADC 40, SUP 4, JG 3, MID 2).
Fail rate = share of player-games that would fail the proposed rule. Win
rates compare fail vs. pass groups (association only, not causal; n≈100 per
role, so ±10pp is noise).

| Rule | TOP | JG | MID | ADC | SUP |
|---|---|---|---|---|---|
| A1 fail rate, proposed `max_level_deficit: 0` | 42% | 29% | 28% | 30% | 29% |
| A1 fail rate, current `max_level_deficit: 1` | 14% | 7% | 8% | 2% | 4% |
| A1 win rate fail / pass | 43 / 55 | 21 / 62 | 50 / 50 | 30 / 59 | 21 / 62 |
| A2 fail rate, ≥2 deaths before 14:00 | 47% | 44% | 53% | 46% | 49% |
| A2 win rate fail / pass | 47 / 53 | 36 / 61 | 43 / 57 | 39 / 59 | 43 / 57 |
| B1 fail rate, ≥1000g for 2+ frames (≥3 frames) | 14% (6%) | 54% (22%) | 21% (0%) | 23% (7%) | 4% (1%) |
| B1 win rate fail / pass | 36 / 52 | 57 / 41 | 48 / 51 | 61 / 47 | — (n=4) |
| B3 control wards placed per 10 min, median (p25–p75) | 0.3 (0–0.7) | 0.6 (0.3–1.2) | 0.5 (0–1.1) | 0.3 (0–0.6) | 2.0 (1.1–2.6) |

Jungle-only (B2): jungle CS at 3:00 median 20 (p25 16), at 4:00 median 25
(p25 24); first back median 4:02 (p25 3:44, p75 4:36) with median 932 gold
at the back frame — consistent with the source's 800–900g first back.

### Reading the results
- **A1** separates winners from losers clearly for JG/ADC/SUP (~30–40pp),
  weakly for TOP, not at all for MID at this sample size. Tightening to 0
  roughly doubles–triples the fail rate to ~30%.
- **A2** fails about half of all player-games (median lane deaths ≈ 1) but
  tracks a consistent ~15–25pp win-rate gap. Strict as a "pass bar"; it
  matches the source's own definition of a lost lane.
- **B1 is confounded:** for JG/ADC, holding ≥1000g is associated with
  *winning* — players who are ahead earn gold faster than they can recall.
  As written it does not isolate "forgot to recall". Keep 🟡; consider the
  3-frame variant or condition on not-ahead before enabling.
- **B3:** the source implies ~1 control ward per objective (~2 per 10 min)
  for everyone; only supports reach that today. Thresholds need a decision.

### Applied (2026-11-17) and resulting pass rates
Decisions: A1 → 0 for TOP/JG/MID/SUP; A2 implemented with max 1; B3 tiered
targets; B2 implemented; B1 deferred (confounded). Pass rates of the new
rules over the same 50 games (all participants of that role):

| Rule | TOP | JG | MID | SUP |
|---|---|---|---|---|
| `control_ward_rate` | 35% | 29% | 53% | 50% |
| `jungle_first_clear` | — | 61% → 74% with early-gank exemption | — | — |

`jungle_first_clear` spend estimate (frame gold delta around the first shop
trip) was cross-checked against Data Dragon prices: it matches the items'
`total` cost (e.g. 900 = Giant's Belt), i.e. the estimator is accurate.

### Early-death cutoff check (2026-11-17)
Question: is 8:00 the right cutoff for `deaths_before_minute`? The user keeps
the deliberate overlap with `deaths_in_lane_phase` (early deaths weigh on the
rest of the lane, jungle included). Same 50 games, all players.

**Cutoff sweep, `max_deaths: 1`** (current) — fail rate / win rate fail vs pass:

| T | 4 | 5 | 6 | 7 | **8** | 9 | 10 | 12 |
|---|---|---|---|---|---|---|---|---|
| All roles | 1% / 29 vs 50 | 4% / 33 vs 51 | 7% / 33 vs 51 | 10% / 35 vs 52 | **15% / 33 vs 53** | 19% / 40 vs 52 | 27% / 42 vs 53 | 39% / 40 vs 57 |
| Jungle | 1% / 0 vs 51 | 4% / 25 vs 51 | 4% / 25 vs 51 | 10% / 40 vs 51 | **13% / 38 vs 52** | 14% / 36 vs 52 | 26% / 46 vs 51 | 36% / 39 vs 56 |

With `max_deaths: 0` the rule fails 47% at 8:00 with only an 8pp win-rate
gap — it would just duplicate `deaths_in_lane_phase`.

**Per-death cost by minute** (OLS on gold diff @14 vs. lane opponent,
controlling for kills/assists before 14:00; 90% bootstrap CI): lanes −483
(0–4), −201 (4–6), −365 (6–8), −351 (8–10), −284 (10–12), −408 (12–14);
jungle ≈ −510 to −620 from 4:00 on (0–4: −129, n=17, CI spans 0). Win-prob
costs are −3 to −10pp per death with overlapping CIs.

**Conclusion:** keep `before_minute: 8, max_deaths: 1` for all roles. One
death costs about the same whenever it happens in laning; what 8:00 + max 1
captures best is *dying twice early*, which separates outcomes most sharply
(≈20pp win-rate gap) at a reasonable 13–15% fail rate.
