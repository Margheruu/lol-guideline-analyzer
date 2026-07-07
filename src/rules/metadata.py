"""Per-rule data-provenance notes, for UI display.

Not evaluation logic — documents the timing/granularity of the underlying
data each rule reads (e.g. "this HP value is from the 60s frame before the
death, not the instant of death"), so the app can show it next to the
verdict. Keyed by rule id (see registry.py); not every rule needs an entry.
"""
from __future__ import annotations

DATA_NOTES: dict[str, str] = {
    "cs_per_minute":
        "指定した分の60秒フレーム時点のCSを使用（フレーム境界のスナップショット）。",
    "not_behind_at_minute":
        "指定した分の60秒フレーム時点のゴールド・CS・レベル差を使用。",
    "deaths_before_minute":
        "デスイベントのタイムスタンプ（ミリ秒精度）を分単位の閾値と比較。",
    "isolated_deaths":
        "デス位置はイベントで正確。味方位置はデス直前の60秒フレーム時点のため、"
        "最大60秒古い可能性がある。",
    "low_hp_deaths":
        "HPはデス直前の60秒フレーム時点の値。デスの瞬間ではなく、"
        "最大60秒古い可能性がある。",
    "frontmost_deaths":
        "味方位置はデス直前の60秒フレーム時点のため、最大60秒古い可能性がある。",
    "death_cause_summary":
        "ダメージ内訳はデスイベントに付随する数値のため正確（フレーム由来ではない）。",
    "boots_type_match":
        "被ダメージ内訳は試合終了時点のポストゲーム集計値（時系列の変化は追えない）。",
    "kill_participation":
        "試合終了時点のポストゲーム集計値（Riot公式 challenges 統計）。",
    "wards_per_interval":
        "WARD_PLACEDイベントのタイムスタンプ（ミリ秒精度）を使用。",
}
