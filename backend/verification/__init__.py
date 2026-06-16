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
    check_against_afn,
)
from backend.verification.sample_set import (
    SampleVerdict,
    SampleSetResult,
    verify_samples,
)

__all__ = [
    "EquivalenceResult",
    "check_equivalence",
    "check_against_regex",
    "check_against_afn",
    "SampleVerdict",
    "SampleSetResult",
    "verify_samples",
]
