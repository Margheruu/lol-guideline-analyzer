"""Sanity checks for the per-role guideline config files."""
from __future__ import annotations

from pathlib import Path

import pytest

import src.rules  # noqa: F401  (register rule modules)
from src.eval.roles import ROLE_KEYS, guidelines_filename
from src.eval.runner import load_guidelines
from src.rules import registry

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


@pytest.mark.parametrize("role_key", ROLE_KEYS)
def test_guideline_file_loads_and_resolves(role_key):
    path = CONFIG_DIR / guidelines_filename(role_key)
    guidelines = load_guidelines(path)

    assert guidelines, f"{path.name} has no rules"
    for g in guidelines:
        registry.get(g["id"])  # raises KeyError with the bad id if unknown
