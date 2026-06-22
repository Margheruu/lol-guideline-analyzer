# Rule Roadmap

Master ledger of guideline rules derived from the user's ADC guidelines PDF.
v1 uses the official Riot API only (post-game stats + 60s timeline frames +
events). See `CLAUDE.md` for data limits.

Status legend: ✅ implemented · 🔜 planned (v1) · 🟡 measurable but noisy
(coarse 60s positions / approximations) · ⛔ out of v1 scope.

## A. Laning fundamentals
| Rule | Checks | PDF source | Signal | Status |
|---|---|---|---|---|
| `cs_at_minute` | CS target at a minute | matchup CS goals | participantFrames.minionsKilled | ✅ |
| `cs_diff_vs_opponent` | CS vs same-role opponent | "win CS / stay even" | frame × opponent | 🔜 |
| `not_behind_at_minute` | not gold-behind at 15:00 | lane lead/deficit | frame totalGold × opp | ✅ |
| `level_spike_timing` | Lv2/Lv3 timing | "Lv3 = 4th wave melee" | LEVEL_UP events | 🟡 |
| `deaths_before_minute` | early deaths | "don't die" | CHAMPION_KILL victim | ✅ |
| `deaths_in_lane_phase` | total lane-phase deaths | "don't die" | CHAMPION_KILL victim | 🔜 |

## B. Death analysis (PDF's most-repeated theme — p5 "analyze your deaths")
| Rule | Checks | PDF source | Signal | Status |
|---|---|---|---|---|
| `deaths_for` (analysis) | per-death record: pos, HP%, killer, top damage, allies nearby | "analyze death reasons" | CHAMPION_KILL + nearest frame championStats | ✅ |
| `isolated_deaths` | deaths with no ally nearby | "don't walk first / when alone" | kill pos × allies' frame pos | ✅ |
| `low_hp_deaths` | deaths after already being low HP | "weak at low-HP laning" | championStats.health before death | ✅ |
| `frontmost_deaths` | died as the most-forward player | "never be the front line" | kill pos × allies' pos | 🟡 (info only for now) |
| `death_cause_summary` | damage-type / killer breakdown | "improve per cause" | victimDamageReceived | 🔜 |

## C. Vision / participation / objectives
| Rule | Checks | PDF source | Signal | Status |
|---|---|---|---|---|
| `wards_per_interval` | wards placed per interval | "river push vision" | WARD_PLACED events | 🔜 |
| `kill_participation` | K+A / team kills | "join more fights" | match stats | 🔜 |
| `objective_participation` | near dragon/herald/turret events | "objective fights = snowball" | ELITE_MONSTER/BUILDING_KILL pos×time | 🟡 |

## D. Itemization
| Rule | Checks | PDF source | Signal | Status |
|---|---|---|---|---|
| `boots_type_match` | defensive boot resist type | "armor boots vs AD" | damageTaken type × boots | ✅ |
| `defensive_item_type_match` | armor/MR item type fit | "defensive items" | damageTaken × ddragon item tags | 🟡 |

## E. Recall (secondary signal)
| Rule | Checks | PDF source | Signal | Status |
|---|---|---|---|---|
| `recall_jg_context` | reward recalls when enemy JG bot + ally JG top | recall rule #1 | recall inference × JG position | 🟡 |

## ⛔ Out of v1 scope (recorded, not built)
- **Champion-specific** combos/builds (Caitlyn/Kai'Sa/etc.) — by decision.
- **Mechanics & judgment** not in data: kiting, sidestep, camera, cursor,
  baiting, "stay calm", "plan your exit".
- **Team comms / pings / requests** to SUP/JG.
- **Summoner-spell usage** (Flash etc.) — not in API → Phase 2 (replay).
- **Wave-management micro** (freeze/pull-wave crafting) — unreliable at 60s
  resolution → revisit in Phase 2 with advanced wave-state inference.
