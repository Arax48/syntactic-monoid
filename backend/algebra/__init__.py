"""
backend.algebra
===============

Algebraic analysis: transition monoid, homomorphism, group theory, Green's relations.
"""

from backend.algebra.transition_monoid import TransitionMonoid
from backend.algebra.homomorphism import Homomorphism
from backend.algebra.group_analysis import GroupAnalysis, analyze

__all__ = ["TransitionMonoid", "Homomorphism", "GroupAnalysis", "analyze"]
