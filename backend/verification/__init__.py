"""
backend.verification
====================

Automata equivalence checking and correctness verification against
language specifications.
"""

from backend.verification.equivalence import (
    EquivalenceResult,
    check_equivalence,
    check_against_regex,
    check_against_nfa,
)

__all__ = [
    "EquivalenceResult",
    "check_equivalence",
    "check_against_regex",
    "check_against_nfa",
]
