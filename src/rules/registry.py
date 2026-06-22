"""Registry mapping rule ids (used in guidelines.yaml) to rule functions."""
from __future__ import annotations

from typing import Callable

from .base import Rule

_REGISTRY: dict[str, Rule] = {}


def register(rule_id: str) -> Callable[[Rule], Rule]:
    """Decorator: register a rule function under ``rule_id``."""

    def deco(fn: Rule) -> Rule:
        if rule_id in _REGISTRY:
            raise ValueError(f"duplicate rule id: {rule_id}")
        _REGISTRY[rule_id] = fn
        return fn

    return deco


def get(rule_id: str) -> Rule:
    if rule_id not in _REGISTRY:
        raise KeyError(f"unknown rule id: {rule_id}")
    return _REGISTRY[rule_id]


def all_rules() -> dict[str, Rule]:
    return dict(_REGISTRY)
