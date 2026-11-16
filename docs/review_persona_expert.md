# Expert Reviewer Persona & Environment Check

A reusable review lens for checking that guideline rules still fit the
**current game environment** — meaning season-level system changes
(objectives, role quests, item systems), *not* patch-by-patch balance.
Re-run this review when a major systems change lands (e.g. a new season).

> The persona is a structured lens applied by the analyst, not the opinion
> of a real expert. Environment facts below are measured from match data.

## Persona
- **Profile:** JP server Master (peak Grandmaster), 10+ seasons, mains
  Jungle/Mid, comfortable on all roles; coaches Silver–Diamond players.
- **Focus:** season-level systems over patch numbers; macro and tempo over
  micro; skeptical of beginner heuristics being enforced as hard rules.
- **Review questions (per rule):**
  1. Is the rule still true under the current systems?
  2. Does it punish correct play (false positive)?
  3. Does it miss the real mistake (false negative)?
  4. Is the threshold right for the target rank bracket?

## Environment fact sheet

**Data:** cached matches in `data/raw/` — 57 games, gameVersion 16.12–16.14
(patches 26.12–26.14), played 2026-06-18 → 2026-07-20. Discord guide posts
are from 2024-08 – 2024-10.

| Topic | Discord guide (2024) | Current (2026 data) | Evidence |
|---|---|---|---|
| Void Grubs | spawn 6:00, gone at 14:00 | **spawn 8:00, a single wave of 3** | exactly 3 kills in all 57 games; earliest kill 8:07 |
| Rift Herald | spawns 14:00 (bot↔mid swap at 14:00 for it) | **spawns ~15:00** | earliest kill 15:19 (46 games) |
| Baron | 20:00 | consistent with 20:00 | earliest kill 21:37 (27 games) |
| Atakhan | — | **absent** | 0 of 452 elite-monster kills |
| Dragon | 5:00 | unchanged | earliest kill 5:28 |
| Turret plates | fall at 14:00 (basis for "laning = 0–14 min") | **persist past 14:00** | 72% of 2,509 plate kills after 14:00; latest 48:39 |
| Support item | buy World Atlas at start | **auto-granted** — never purchased (only `ITEM_DESTROYED` 3865→3866→3867) | role-bound slot holds a control ward for 82/114 supports |
| Role quests | — | **every role has one** (`roleBoundItem`): TOP → Unleashed Teleport, ADC → boots in the role slot, JG/MID/SUP quest rewards | match `participants[].roleBoundItem` |
| Teleport | TOP and MID carry TP | MID 74% TP; TOP only 49% (TP comes from the quest) | summoner spells |
| First outer turret | marks mid-game start | median 14.7 min (p10 12.8) | `BUILDING_KILL` |
| JG first back | after full clear, 800–900g | unchanged: median 4:02, 932g | frames + purchases |

## Rule review (2026-11-17)

| Rule | Verdict | Notes |
|---|---|---|
| `cs_per_minute`, `kill_participation`, death-analysis rules, `wards_per_interval` | ✅ | environment-neutral |
| `not_behind_at_minute` (level deficit 0) | ✅ | TOP quest XP is symmetric between lane opponents |
| `control_ward_rate` | ✅ | SUP target 2.0 is measured in the current role-slot-ward environment (median 2.0) |
| `deaths_in_lane_phase` (14:00) | ✅ after fix | rationale rewritten: plates no longer fall at 14:00, but the first outer turret does (median 14.7) |
| `deaths_before_minute` + `deaths_in_lane_phase` | ⚠ open | a death before 8:00 counts in both rules. Keep only if early deaths should weigh double — **pending user decision** |
| `boots_type_match` (ADC) | ⚠ info | ADC boots sit in the role slot and no ADC built defensive boots in the data, so it rarely evaluates |
| `jungle_first_clear` | ✅ after fix | added `exempt_if_takedown_by_minute: 4` so converted early-gank paths are not flagged (exempts 29/100 junglers; pass 61% → 74%) |

### Impact on planned rules
- **`objective_setup` (B4):** use current spawn times — dragon 5:00,
  grubs 8:00 (single wave), herald 15:00, baron 20:00; no Atakhan. Do not
  use the Discord timings.
- **`support_item_completion` (B5):** there is no purchase event any more;
  use the `ITEM_DESTROYED` time of World's Bounty (3867) — the moment the
  final support item is chosen (final-item purchase median ~13.7 min).
- **ADC bot↔mid swap proposal:** the "swap at 14:00 for herald" rationale
  is outdated (herald ~15:00). Proposal only; ADC config untouched.
