"""
backend.verification.sample_set
================================

Verificacion por listas de ejemplos: el estudiante suministra dos
listas — `accept` (palabras que el automata DEBE aceptar) y `reject`
(palabras que DEBE rechazar) — y la herramienta corre cada palabra
sobre el automata, comparando contra el veredicto esperado.

Esto es complementario a la equivalencia simbolica de
`backend.verification.equivalence`: aquella decide L(A) = L(B) para
lenguajes regulares, mientras que la verificacion por muestras se
puede aplicar a CUALQUIER automata simulable — incluyendo PDAs y
maquinas de Turing en slices posteriores donde la equivalencia es
indecidible y solo nos queda el testeo basado en propiedades.

Para automatas finitos (DFA/NFA) tambien sigue siendo util:
pedagogicamente, "estos diez ejemplos no funcionan" es mas concreto
que un contraejemplo abstracto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Protocol


# ----------------------------------------------------------------------
# Protocolo: cualquier objeto con .accepts(str) -> bool
# ----------------------------------------------------------------------

class _Acceptor(Protocol):
    def accepts(self, word: str) -> bool: ...


# ----------------------------------------------------------------------
# Resultados
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SampleVerdict:
    """Veredicto de una sola palabra de la muestra."""

    word: str
    expected: bool          # True si se esperaba aceptar, False si rechazar.
    actual: Optional[bool]  # Veredicto real; None si hubo un error.
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        """True si el automata respondio lo que se esperaba."""
        return self.error is None and self.actual == self.expected


@dataclass(frozen=True)
class SampleSetResult:
    """Agregado de veredictos sobre una muestra completa."""

    verdicts: List[SampleVerdict] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.verdicts)

    @property
    def passed(self) -> int:
        return sum(1 for v in self.verdicts if v.ok)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def all_pass(self) -> bool:
        return self.failed == 0 and self.total > 0

    @property
    def mismatches(self) -> List[SampleVerdict]:
        """Solo los veredictos que NO coincidieron con lo esperado."""
        return [v for v in self.verdicts if not v.ok]

    def summary(self, name: str = "automata") -> str:
        """Mensaje legible en castellano, listo para mostrar al estudiante."""
        if self.total == 0:
            return f"No se evaluo ninguna palabra contra el {name}."
        if self.all_pass:
            return (
                f"✓ {self.passed}/{self.total} palabras coincidieron con lo "
                f"esperado. El {name} se comporta correctamente sobre la "
                f"muestra."
            )
        lineas = [
            f"✗ {self.passed}/{self.total} palabras coincidieron con lo "
            f"esperado. {self.failed} discrepan:",
        ]
        for v in self.mismatches:
            w = "ε" if v.word == "" else repr(v.word)
            if v.error is not None:
                lineas.append(f"  - {w}: error ({v.error}).")
                continue
            quer = "aceptar" if v.expected else "rechazar"
            dio = "acepto" if v.actual else "rechazo"
            lineas.append(
                f"  - {w}: se esperaba {quer}, el {name} {dio}."
            )
        return "\n".join(lineas)

    def pretty_table(self) -> str:
        """Tabla monoespaciada con columnas palabra/esperado/actual/ok."""
        if self.total == 0:
            return "(muestra vacia)"
        header = ("palabra", "esperado", "actual", "ok")
        rows: List[tuple[str, str, str, str]] = []
        for v in self.verdicts:
            w = "ε" if v.word == "" else v.word
            esp = "acepta" if v.expected else "rechaza"
            if v.error is not None:
                act = f"error: {v.error}"
            else:
                act = "acepta" if v.actual else "rechaza"
            ok = "✓" if v.ok else "✗"
            rows.append((w, esp, act, ok))
        widths = [
            max(len(header[i]), max(len(r[i]) for r in rows))
            for i in range(4)
        ]
        out: List[str] = []
        cells = [c.ljust(widths[i]) for i, c in enumerate(header)]
        out.append(" | ".join(cells))
        out.append("-+-".join("-" * w for w in widths))
        for row in rows:
            cells = [c.ljust(widths[i]) for i, c in enumerate(row)]
            out.append(" | ".join(cells))
        return "\n".join(out)


# ----------------------------------------------------------------------
# Verificador
# ----------------------------------------------------------------------

def verify_samples(
    automaton: _Acceptor,
    accept: Iterable[str] = (),
    reject: Iterable[str] = (),
) -> SampleSetResult:
    """Ejecuta `automaton` sobre cada palabra de las dos muestras.

    Captura los `ValueError` que el automata lance ante simbolos fuera
    del alfabeto, marcandolos como errores en el veredicto en lugar
    de propagar la excepcion. Asi el estudiante recibe un reporte
    completo, no un stacktrace tras el primer simbolo invalido.
    """
    verdicts: List[SampleVerdict] = []
    for word in accept:
        verdicts.append(_evaluate(automaton, word, expected=True))
    for word in reject:
        verdicts.append(_evaluate(automaton, word, expected=False))
    return SampleSetResult(verdicts=verdicts)


def _evaluate(automaton: _Acceptor, word: str, expected: bool) -> SampleVerdict:
    try:
        actual = automaton.accepts(word)
    except ValueError as exc:
        return SampleVerdict(
            word=word,
            expected=expected,
            actual=None,
            error=str(exc),
        )
    return SampleVerdict(word=word, expected=expected, actual=actual)


__all__ = [
    "SampleVerdict",
    "SampleSetResult",
    "verify_samples",
]
