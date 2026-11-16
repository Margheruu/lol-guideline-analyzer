# Rule Roadmap

Master ledger of guideline rules. Sources:
- **PDF** — the user's ADC guidelines PDF (authoritative for ADC).
- **Discord** — the lane guides from the user's LoL Discord server (local
  copy in `docs/discord/`, gitignored). Section refs (`Common ⑯`, `JG ③`, …)
  and the full mapping + pass-rate check live in `docs/rule_mapping.md`.
  Discord-only items for ADC are proposals, not applied to ADC config.
- **Environment check** — `docs/review_persona_expert.md` (expert persona +
  measured 2026 fact sheet). Re-run on major system changes.

v1 uses the official Riot API only (post-game stats + 60s timeline frames +
events). See `CLAUDE.md` for data limits.

Status legend: ✅ implemented · 🔜 planned (v1) · 🟡 measurable but noisy
(coarse 60s positions / approximations) · ⛔ out of v1 scope.

## A. Laning fundamentals
| Rule | Checks | PDF source | Discord source | Signal | Status |
|---|---|---|---|---|---|
| `cs_per_minute` | CS-per-minute target (e.g. 7.5 @15) | matchup CS goals | Common ⑧ (practice-tool 70–90 @10; not used as a live bar) | participantFrames.minionsKilled | ✅ |
| CS vs opponent chart | per-minute CS line + 15-min diff | "win CS / stay even" | — | `cs_series()` × opponent | ✅ (app) |
| `not_behind_at_minute` | not gold/CS/level-behind at 15:00 | lane lead/deficit | Common ⑯ (level deficit ≥1 = lane lost → `max_level_deficit: 0` applied to TOP/JG/MID/SUP) | frame totalGold × opp | ✅ |
| `level_spike_timing` | Lv2/Lv3 timing vs opponents | "Lv3 = 4th wave melee" | ADC ③ (Lv2 race: 6 + 3 melee) | LEVEL_UP events | 🔜 (event-precise for Lv2) |
| `deaths_before_minute` | early deaths | "don't die" | — | CHAMPION_KILL victim | ✅ |
| `deaths_in_lane_phase` | lane-phase deaths (0:00–14:00) | "don't die" | Common ⑯ (2 deaths = lane lost), Common ⑬ (laning = 0–14 min) | CHAMPION_KILL victim | ✅ |
| `gold_hoarding` | recall when holding ≥1000g in lane | — | TOP ② / MID ② / ADC ④ (recall timing #3) | frame currentGold runs | 🟡 (confounded by being ahead) |
| `jungle_first_clear` | full clear, then first back with 800–900g | — | JG ③ | jungleMinionsKilled @4:00 + first-trip spend (frame gold delta); exempt if kill/assist by 4:00 | ✅ |
| `turret_plates` | plates taken in laning | — | Common ⑬ | challenges.turretPlatesTaken | 🔜 (info only) |

## B. Death analysis (PDF's most-repeated theme — p5 "analyze your deaths")
| Rule | Checks | PDF source | Discord source | Signal | Status |
|---|---|---|---|---|---|
| `deaths_for` (analysis) | per-death record: pos, HP%, killer, top damage, allies nearby | "analyze death reasons" | — | CHAMPION_KILL + nearest frame championStats | ✅ |
| `isolated_deaths` | deaths with no ally nearby | "don't walk first / when alone" | Common ⑱ (never fight outnumbered), SUP ② | kill pos × allies' frame pos | ✅ |
| `low_hp_deaths` | deaths after already being low HP | "weak at low-HP laning" | TOP/MID ② recall timing #1 | championStats.health before death | ✅ |
| `frontmost_deaths` | died as the most-forward player | "never be the front line" | Common ㉖ (carry enters late) | kill pos × allies' pos | 🟡 (info only for now) |
| `death_cause_summary` | damage-type / killer breakdown | "improve per cause" | — | victimDamageReceived | ✅ |
| `side_lane_overextension` | mid-game deaths past the side-lane midpoint, alone | — | TOP ④ / MID ⑤ | death pos zone × allies × t≥14:00 | 🟡 |
| `fighting_while_behind` | deaths after the lane is already lost | — | Common ⑯ | lane-lost state × later deaths | 🟡 |

## C. Vision / participation / objectives
| Rule | Checks | PDF source | Discord source | Signal | Status |
|---|---|---|---|---|---|
| `wards_per_interval` | wards placed per interval | "river push vision" | — | WARD_PLACED events | ✅ |
| `control_ward_rate` | control wards placed per 10 min | — | Common ㉕ (one each per objective setup) | challenges.controlWardsPlaced | ✅ |
| `kill_participation` | K+A / team kills | "join more fights" | — | match stats | ✅ |
| `objective_participation` | near dragon/herald/turret events | "objective fights = snowball" | TOP/MID/ADC "take objectives after winning lane" | ELITE_MONSTER/BUILDING_KILL pos×time | 🟡 |
| `objective_setup` | regroup before spawn (recall at T-1:30–1:00, at pit by T-0:20) | — | Common ㉕ | spawn timers × frame pos — use current spawns (dragon 5:00, grubs 8:00, herald 15:00, baron 20:00; no Atakhan), not the guide's | 🟡 |

## D. Itemization
| Rule | Checks | PDF source | Discord source | Signal | Status |
|---|---|---|---|---|---|
| `boots_type_match` | defensive boot resist type | "armor boots vs AD" | — | damageTaken type × boots | ✅ |
| core item timing | core-item completion vs opponent | "対面とのコアアイテム比較" | Common ⑯ (opponent core first = lane lost → promote to verdict) | timeline ITEM_PURCHASED (all players) × ddragon | ✅ (app) |
| `support_item_completion` | support quest completion vs enemy SUP | — | SUP ① | `ITEM_DESTROYED` of World's Bounty (3867) — support item is auto-granted, no purchase event | 🔜 |
| `defensive_item_type_match` | armor/MR item type fit | "defensive items" | — | damageTaken × ddragon item tags | 🟡 |

## E. Recall (secondary signal)
| Rule | Checks | PDF source | Discord source | Signal | Status |
|---|---|---|---|---|---|
| `recall_jg_context` | reward recalls when enemy JG bot + ally JG top | recall rule #1 | — | recall inference × JG position | 🟡 |

## ⛔ Out of v1 scope (recorded, not built)
- **Champion-specific** combos/builds (Caitlyn/Kai'Sa/etc.) — by decision.
- **Mechanics & judgment** not in data: kiting, sidestep, camera, cursor,
  baiting, "stay calm", "plan your exit"; Discord: trade patterns, skill
  dodging, triangle rule, minimap frequency, team-comp / formation, focus,
  end-game calls.
- **Team comms / pings / requests** to SUP/JG (incl. Discord gank setup).
- **Ward placement location** (dragon-pit control ward, bush wards, baron
  pit) — `WARD_PLACED` has no position.
- **Summoner-spell usage** (Flash etc.) — not in API → Phase 2 (replay).
- **Wave-management micro** (freeze/pull-wave crafting) — unreliable at 60s
  resolution → revisit in Phase 2 with advanced wave-state inference.
