"""Rule framework.

Each guideline is implemented as a small, pure, testable function that takes a
normalized ``MatchContext`` plus its parameters and returns a ``RuleResult``.
Keeping rules pure (no I/O) makes them trivial to unit-test on saved sample
timelines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Evidence:
    """A single piece of supporting evidence for a rule verdict."""

    detail: str
    timestamp_ms: int | None = None
    position: dict[str, float] | None = None


@dataclass
class RuleResult:
    rule_id: str
    passed: bool
    score: float  # 0..1; how well the guideline was met
    message: str
    evidence: list[Evidence] = field(default_factory=list)


@dataclass
class MatchContext:
    """Normalized view of one player's match, built from match + timeline.

    ``participant_id`` is the 1-based id used inside the timeline; map it from
    ``puuid`` via the match ``metadata.participants`` order.
    """

    match_id: str
    puuid: str
    participant_id: int
    match: dict[str, Any]
    timeline: dict[str, Any]


# A rule: (context, params) -> result.
Rule = Callable[[MatchContext, dict[str, Any]], RuleResult]
