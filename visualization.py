"""
visualization.py
================

Utilidades de visualizacion y exportacion de reportes:

    * render_dfa            : grafo del DFA en formato PNG/PDF/DOT (Graphviz).
    * render_cayley_table   : tabla de Cayley como imagen PNG (matplotlib).
    * render_class_diagram  : diagrama de clases de equivalencia (matplotlib).
    * write_report          : reporte completo en texto plano / markdown.

Las dependencias graphviz y matplotlib son opcionales: si no estan
disponibles, se levanta una excepcion clara con instrucciones de
instalacion. Esto permite que el resto del proyecto siga siendo
ejecutable en entornos sin librerias graficas (por ejemplo, CI minimo).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from dfa import DFA
from algebra import Homomorphism
from transition_monoid import TransitionMonoid


# ----------------------------------------------------------------------
# DFA -> Graphviz
# ----------------------------------------------------------------------

def render_dfa(
    dfa: DFA,
    output_path: str | Path,
    fmt: str = "png",
    view: bool = False,
) -> Path:
    """Renderiza el DFA como un grafo dirigido usando Graphviz.

    Parametros
    ----------
    dfa : DFA
    output_path : str | Path
        Ruta SIN extension donde guardar el archivo (Graphviz anade la
        extension correspondiente al formato).
    fmt : str
        Formato de salida ("png", "pdf", "svg", "dot", ...).
    view : bool
        Si True, abre el archivo con el visor del sistema operativo.

    Devuelve
    --------
    Path : ruta absoluta al archivo generado (incluyendo extension).
    """
    try:
        import graphviz  # type: ignore
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            "El paquete 'graphviz' no esta instalado. Ejecute "
            "`pip install graphviz` y asegurese de tener el binario "
            "graphviz disponible en PATH."
        ) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dot = graphviz.Digraph(name=dfa.name, format=fmt)
    dot.attr(rankdir="LR", labelloc="t", label=dfa.name)
    dot.attr("node", fontname="Helvetica")
    dot.attr("edge", fontname="Helvetica")

    # Estado inicial invisible para dibujar la flecha entrante.
    dot.node("__start__", shape="none", label="", width="0", height="0")

    for q in sorted(dfa.states):
        shape = "doublecircle" if q in dfa.accepting else "circle"
        dot.node(q, shape=shape)

    dot.edge("__start__", dfa.start)

    # Agrupa los simbolos que comparten origen y destino.
    for q in sorted(dfa.states):
        bucket: dict[str, list[str]] = {}
        for a in sorted(dfa.alphabet):
            target = dfa.transitions[q][a]
            bucket.setdefault(target, []).append(a)
        for target, symbols in bucket.items():
            dot.edge(q, target, label=", ".join(symbols))

    rendered = dot.render(filename=str(output_path), view=view, cleanup=True)
    return Path(rendered)


# ----------------------------------------------------------------------
# Tabla de Cayley -> matplotlib
# ----------------------------------------------------------------------

def render_cayley_table(
    monoid: TransitionMonoid,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Renderiza la tabla de Cayley como una imagen PNG.

    Cada celda contiene la etiqueta del producto correspondiente. La
    fila/columna 0 corresponde a la identidad y las restantes a los
    representantes minimos de cada clase.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")  # backend sin pantalla
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            "El paquete 'matplotlib' no esta instalado. Ejecute "
            "`pip install matplotlib`."
        ) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    table = monoid.cayley_table()
    labels = monoid.labels()
    n = len(labels)

    fig_size = max(4.0, 0.6 * n + 1.5)
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("g")
    ax.set_ylabel("f")
    if title:
        ax.set_title(title)
    else:
        ax.set_title(f"Tabla de Cayley de M({monoid.dfa.name})")

    # Pintamos una rejilla.
    for i in range(n + 1):
        ax.axhline(i - 0.5, color="lightgray", linewidth=0.5)
        ax.axvline(i - 0.5, color="lightgray", linewidth=0.5)

    for i in range(n):
        for j in range(n):
            ax.text(
                j,
                i,
                labels[table[i][j]],
                ha="center",
                va="center",
                fontsize=9,
            )

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(n - 0.5, -0.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


# ----------------------------------------------------------------------
# Diagrama de clases de equivalencia
# ----------------------------------------------------------------------

def render_class_diagram(
    hom: Homomorphism,
    output_path: str | Path,
    max_length: int = 3,
) -> Path:
    """Diagrama de barras que muestra el tamano de cada clase de
    equivalencia (truncada a palabras de longitud <= max_length).
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "El paquete 'matplotlib' no esta instalado. Ejecute "
            "`pip install matplotlib`."
        ) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cls = hom.kernel(max_length=max_length)
    labels = []
    sizes = []
    for f in hom.monoid.elements:
        rep = hom.monoid.representatives[f]
        labels.append("e" if rep == "" else rep)
        sizes.append(len(cls[f]))

    fig, ax = plt.subplots(figsize=(max(6.0, 0.45 * len(labels) + 2), 4))
    ax.bar(labels, sizes, color="steelblue", edgecolor="black")
    ax.set_xlabel("Representante minimo de la clase")
    ax.set_ylabel(
        f"# palabras con |w| <= {max_length} en la clase"
    )
    ax.set_title(
        f"Clases de equivalencia de Ker(phi) - {hom.dfa.name}"
    )
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


# ----------------------------------------------------------------------
# Reporte de texto
# ----------------------------------------------------------------------

def write_report(
    dfa: DFA,
    output_path: str | Path,
    max_length: int = 3,
) -> Path:
    """Genera un reporte de texto plano con un resumen completo.

    Incluye:
        * Definicion del DFA y tabla de transiciones.
        * Monoide de transicion (transformaciones, identidad, orden).
        * Tabla de Cayley.
        * Clases de equivalencia (Ker phi) hasta longitud max_length.
        * Verificacion empirica del Primer Teorema del Isomorfismo.
    """
    monoid = TransitionMonoid(dfa)
    hom = Homomorphism(dfa, monoid)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    parts.append("=" * 72)
    parts.append(f"REPORTE - {dfa.name}")
    parts.append("=" * 72)
    parts.append("")
    parts.append("DEFINICION DEL DFA")
    parts.append("-" * 72)
    parts.append(f"  Q       = {sorted(dfa.states)}")
    parts.append(f"  Sigma   = {sorted(dfa.alphabet)}")
    parts.append(f"  q0      = {dfa.start}")
    parts.append(f"  F       = {sorted(dfa.accepting)}")
    parts.append("")
    parts.append("Tabla de transiciones:")
    parts.append(dfa.pretty_transition_table())
    parts.append("")
    parts.append("MONOIDE DE TRANSICION M(A)")
    parts.append("-" * 72)
    parts.append(monoid.summary())
    parts.append("")
    parts.append("Elementos (representante : transformacion):")
    for i, f in enumerate(monoid.elements):
        rep = monoid.representatives[f]
        label = "e" if rep == "" else rep
        parts.append(f"  {i:>3}  {label:<6}  {f}")
    parts.append("")
    parts.append("Tabla de Cayley:")
    parts.append(monoid.pretty_cayley_table())
    parts.append("")
    parts.append(f"NUCLEO Y CLASES DE EQUIVALENCIA (|w| <= {max_length})")
    parts.append("-" * 72)
    parts.append(hom.kernel_report(max_length=max_length))
    parts.append("")
    parts.append("VERIFICACION EMPIRICA")
    parts.append("-" * 72)
    parts.append(
        f"  phi(uv) = phi(u).then(phi(v))         : "
        f"{hom.verify_homomorphism(max_length=max_length)}"
    )
    parts.append(
        f"  Sigma*/Ker(phi)  ~=  M(A)             : "
        f"{hom.verify_first_isomorphism()}"
    )
    parts.append("")
    parts.append("=" * 72)

    output_path.write_text("\n".join(parts), encoding="utf-8")
    return output_path


__all__ = [
    "render_dfa",
    "render_cayley_table",
    "render_class_diagram",
    "write_report",
]
