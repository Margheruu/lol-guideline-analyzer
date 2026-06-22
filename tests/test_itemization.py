"""Unit tests for boots_type_match (high-precision boot-type check)."""
from __future__ import annotations

from src.rules.itemization import boots_type_match

STEELCAPS, MERCS, BERSERKERS = 3047, 3111, 3006


def test_correct_armor_boots_vs_physical(make_ctx):
    # 70% physical damage taken + Plated Steelcaps -> correct.
    ctx = make_ctx(phys=7000, magic=2000, true=1000, boot_ids=(STEELCAPS,))
    res = boots_type_match(ctx, {"threshold": 0.6})
    assert res.passed is True


def test_wrong_mr_boots_vs_physical(make_ctx):
    # 70% physical but built Mercury's Treads -> mismatch.
    ctx = make_ctx(phys=7000, magic=2000, true=1000, boot_ids=(MERCS,))
    res = boots_type_match(ctx, {"threshold": 0.6})
    assert res.passed is False
    assert "不一致" in res.message


def test_offensive_boots_not_evaluated(make_ctx):
    # Berserker's Greaves is offensive -> not evaluated (passes).
    ctx = make_ctx(boot_ids=(BERSERKERS,))
    res = boots_type_match(ctx, {})
    assert res.passed is True
    assert "評価対象外" in res.message


def test_no_boots_not_evaluated(make_ctx):
    ctx = make_ctx(boot_ids=())
    res = boots_type_match(ctx, {})
    assert res.passed is True
    assert "評価対象外" in res.message


def test_balanced_damage_passes(make_ctx):
    # 50/50 split is below the 0.6 threshold -> either resist boot is fine.
    ctx = make_ctx(phys=5000, magic=5000, true=0, boot_ids=(MERCS,))
    res = boots_type_match(ctx, {"threshold": 0.6})
    assert res.passed is True
