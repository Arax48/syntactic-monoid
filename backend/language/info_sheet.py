"""
backend.language.info_sheet
============================

Hoja informativa para el estudiante.

Dado un AFD, este modulo produce un reporte en castellano con secciones
tematicas que materializan el puente entre TEORIA DE COMPUTACION y
ALGEBRA (Discrete Math II). El objetivo es que tras CONSTRUIR o
VERIFICAR un automata el estudiante reciba un resumen que conteste:

    * ¿que automata tengo?
    * ¿como es algebraicamente su monoide de transicion M(A)?
    * ¿es M(A) un grupo? si si, ¿cual?
    * ¿que tiene esto que ver con lo que veo en algebra?
    * ¿que cosa "rara" o sorprendente esta pasando aqui?
    * ¿que puedo hacer a continuacion?

Por diseno, este modulo NO infiere descripciones del lenguaje a partir
del AFD (eso es indecidible en general). Lo que si hace es interpretar
algebraicamente la estructura de M(A) y traducirla a frases que un
estudiante de primer semestre pueda leer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from backend.algebra.group_analysis import GroupAnalysis, analyze
from backend.algebra.homomorphism import Homomorphism
from backend.algebra.transition_monoid import TransitionMonoid
from backend.models.afd import AFD


# ----------------------------------------------------------------------
# Constructor
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class InfoSheet:
    """Hoja informativa para un AFD dado."""

    dfa: AFD
    monoid: TransitionMonoid
    homomorphism: Homomorphism
    analysis: GroupAnalysis

    # --- formatos -----------------------------------------------------

    def as_text(self) -> str:
        return "\n".join(_render_text(self))

    def as_markdown(self) -> str:
        return "\n".join(_render_markdown(self))

    def write(self, path: str | Path) -> Path:
        """Escribe la version texto plano a `path`."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.as_text(), encoding="utf-8")
        return p

    def write_markdown(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.as_markdown(), encoding="utf-8")
        return p


def build_info_sheet(dfa: AFD) -> InfoSheet:
    monoid = TransitionMonoid(dfa)
    hom = Homomorphism(dfa, monoid)
    info = analyze(monoid)
    return InfoSheet(dfa=dfa, monoid=monoid, homomorphism=hom, analysis=info)


# ----------------------------------------------------------------------
# Render: texto plano
# ----------------------------------------------------------------------

_BAR = "=" * 64
_SUB = "-" * 64


def _render_text(sheet: InfoSheet) -> List[str]:
    out: List[str] = []
    dfa = sheet.dfa
    m = sheet.monoid
    info = sheet.analysis

    # --- Cabecera -----------------------------------------------------
    out += [_BAR, f"  HOJA INFORMATIVA - {dfa.name}", _BAR, ""]

    # --- 1. El automata ----------------------------------------------
    out += [
        "1. TU AUTOMATA",
        _SUB,
        f"   Nombre  : {dfa.name}",
        f"   |Q|     : {len(dfa.states)}    estados: {{{', '.join(sorted(dfa.states))}}}",
        f"   |Σ|     : {len(dfa.alphabet)}    simbolos: {{{', '.join(sorted(dfa.alphabet))}}}",
        f"   q0      : {dfa.start}",
        f"   F       : {{{', '.join(sorted(dfa.accepting))}}}",
        "",
    ]

    # --- 2. Monoide ---------------------------------------------------
    cota = len(dfa.states) ** len(dfa.states)
    out += [
        "2. MONOIDE SINTACTICO M(A)",
        _SUB,
        f"   |M(A)|        : {info.order}",
        f"   Cota |Q|^|Q|  : {cota}    (M es a lo sumo de este tamano)",
        f"   Identidad     : f_λ = id_Q",
        f"   |Idempotentes|: {info.num_idempotents}",
        f"   |Unidades|    : {info.invertible_count}",
        f"   |Centro Z(M)| : {info.center_size}",
        "",
    ]

    # --- 3. ¿Es grupo? -----------------------------------------------
    out += ["3. ¿ES UN GRUPO?", _SUB]
    if info.is_group:
        out += [
            "   Respuesta     : SI - todo elemento tiene inverso.",
            f"   Es abeliano   : {'si' if info.is_abelian else 'no'}",
            f"   Es ciclico    : {'si' if info.is_cyclic else 'no'}",
        ]
        if info.is_cyclic and info.cyclic_generator_word is not None:
            w = info.cyclic_generator_word
            label = "λ" if w == "" else repr(w)
            out += [f"   Generador     : la palabra {label}"]
        out += ["", f"   Su monoide M(A)  ≅  {info.isomorphic_to}"]
    else:
        out += [
            "   Respuesta     : NO - existen elementos sin inverso.",
            f"   |Unidades| = {info.invertible_count} < |M(A)| = {info.order}",
            f"   Es aperiodico : {'si' if info.is_aperiodic else 'no'}",
        ]
    out.append("")

    # --- 4. Conexiones con algebra -----------------------------------
    out += ["4. CONEXIONES CON DISCRETE MATH II", _SUB]
    out += _connection_paragraphs(sheet)
    out.append("")

    # --- 5. Curiosidades ---------------------------------------------
    out += ["5. CURIOSIDADES", _SUB]
    out += _curiosities(sheet)
    out.append("")

    # --- 6. ¿Y ahora que? --------------------------------------------
    out += ["6. ¿Y AHORA QUE?", _SUB]
    out += _recommendations(sheet)
    out.append("")

    # --- 7. Referencias al libro --------------------------------------
    out += ["7. EN EL LIBRO DE DE CASTRO", _SUB]
    out += _book_references(sheet)

    out += ["", _BAR]
    return out


# ----------------------------------------------------------------------
# Render: Markdown
# ----------------------------------------------------------------------

def _render_markdown(sheet: InfoSheet) -> List[str]:
    dfa = sheet.dfa
    info = sheet.analysis
    out: List[str] = []
    out.append(f"# Hoja informativa — {dfa.name}")
    out.append("")
    out.append("## 1. Tu autómata")
    out.append("")
    out.append(f"- **Nombre:** {dfa.name}")
    out.append(f"- **|Q|:** {len(dfa.states)}  ({', '.join(sorted(dfa.states))})")
    out.append(f"- **|Σ|:** {len(dfa.alphabet)}  ({', '.join(sorted(dfa.alphabet))})")
    out.append(f"- **q₀:** {dfa.start}")
    out.append(f"- **F:** {{{', '.join(sorted(dfa.accepting))}}}")
    out.append("")
    out.append("## 2. Monoide de transición M(A)")
    out.append("")
    cota = len(dfa.states) ** len(dfa.states)
    out.append(f"- **|M(A)|:** {info.order}")
    out.append(f"- **Cota teórica:** |Q|^|Q| = {cota}")
    out.append(f"- **Idempotentes:** {info.num_idempotents}")
    out.append(f"- **Unidades:** {info.invertible_count}")
    out.append(f"- **Centro Z(M):** {info.center_size}")
    out.append("")
    out.append("## 3. ¿Es un grupo?")
    out.append("")
    if info.is_group:
        out.append(f"**Sí.** M(A) ≅ **{info.isomorphic_to}**")
        out.append("")
        out.append(f"- Abeliano: {'sí' if info.is_abelian else 'no'}")
        out.append(f"- Cíclico: {'sí' if info.is_cyclic else 'no'}")
        if info.is_cyclic and info.cyclic_generator_word is not None:
            w = info.cyclic_generator_word
            label = "λ" if w == "" else f"`{w}`"
            out.append(f"- Generador: la palabra {label}")
    else:
        out.append("**No** — existen elementos sin inverso.")
        out.append("")
        out.append(f"- Unidades: {info.invertible_count} < |M(A)| = {info.order}")
        out.append(f"- Aperiódico: {'sí' if info.is_aperiodic else 'no'}")
    out.append("")
    out.append("## 4. Conexiones con Discrete Math II")
    out.append("")
    out += [line.lstrip() if line.startswith("   ") else line
            for line in _connection_paragraphs(sheet)]
    out.append("")
    out.append("## 5. Curiosidades")
    out.append("")
    for line in _curiosities(sheet):
        out.append(line.lstrip() if line.startswith("   ") else line)
    out.append("")
    out.append("## 6. ¿Y ahora qué?")
    out.append("")
    for line in _recommendations(sheet):
        out.append(line.lstrip() if line.startswith("   ") else line)
    out.append("")
    out.append("## 7. En el libro de De Castro")
    out.append("")
    for line in _book_references(sheet):
        out.append(line.lstrip() if line.startswith("   ") else line)
    return out


# ----------------------------------------------------------------------
# Cuerpos de las secciones que dependen de la estructura
# ----------------------------------------------------------------------

def _connection_paragraphs(sheet: InfoSheet) -> List[str]:
    info = sheet.analysis
    if info.is_group and info.is_cyclic:
        n = info.order
        w = info.cyclic_generator_word
        gen_label = "λ" if (w is None or w == "") else f'"{w}"'
        if n == 1:
            clases = "{[0]} (solo una clase, la trivial)"
        elif n == 2:
            clases = "{[0], [1]}"
        elif n == 3:
            clases = "{[0], [1], [2]}"
        else:
            clases = f"{{[0], [1], ..., [{n - 1}]}}"
        # El generador induce una "cuenta" sobre las palabras del alfabeto.
        return [
            f"   El monoide M(A) es CICLICO de orden {n}, es decir,",
            f"   M(A)  ≅  ℤ/{n}ℤ,",
            "   el MISMO objeto que ve en Discrete Math II como las clases",
            f"   de equivalencia {clases} modulo {n}.",
            "",
            f"   * El homomorfismo natural φ : Σ* → M(A) cuenta apariciones",
            f"     del generador {gen_label} modulo {n}.",
            "   * Dos palabras son equivalentes (φ(u) = φ(v))  sii  inducen",
            "     la misma transformacion sobre Q,  sii  caen en la misma",
            f"     clase de residuos modulo {n}.",
            f"   * Las clases del nucleo de φ son exactamente las clases",
            f"     ℤ/{n}ℤ.  Aritmetica modular en vivo.",
        ]
    if info.is_group and info.is_abelian:
        return [
            f"   M(A) es un GRUPO ABELIANO finito de orden {info.order}.",
            "   Esta categoria fue clasificada por Cauchy y Frobenius:",
            "   por el teorema de estructura, M(A) se descompone como",
            "   producto de grupos ciclicos. Concretamente, M(A) ≅",
            f"   {info.isomorphic_to}.",
            "",
            "   * Cada clase del nucleo de φ corresponde a un coset del",
            "     subgrupo trivial — todas las palabras equivalentes son",
            "     'la misma' modulo la suma del grupo abeliano.",
        ]
    if info.is_group and not info.is_abelian:
        return [
            f"   M(A) es un GRUPO NO ABELIANO de orden {info.order}",
            f"   ({info.isomorphic_to}).",
            "",
            "   * El orden de composicion importa: hay palabras u, v",
            "     tales que φ(uv) ≠ φ(vu) aunque ambas sean equivalentes",
            "     a la misma transformacion individualmente.",
            "   * Esto vincula su AFD con teoria de PERMUTACIONES (que es",
            "     el otro gran capitulo de su curso de algebra abstracta).",
        ]
    if not info.is_group and info.is_aperiodic:
        return [
            "   M(A) NO es un grupo, pero ES APERIODICO.",
            "",
            "   Aperiodico (definicion, via Saracino §3 'potencias de un",
            "   elemento'): para todo elemento x de M(A) existe un k tal",
            "   que x^k = x^(k+1); es decir, ninguna palabra genera un",
            "   ciclo no trivial al iterarse.",
            "",
            "   * Equivale a que M(A) no contenga ningun SUBGRUPO no",
            "     trivial (no hay elementos con 'orden' > 1 en el sentido",
            "     de Saracino §3): toda potencia acaba estabilizandose.",
            "   * Contrasta con el caso grupo, donde cada elemento tiene",
            "     inverso y sus potencias recorren un ciclo (Saracino §2).",
        ]
    # Caso por defecto: monoide no grupo y no aperiodico.
    return [
        "   M(A) NO es un grupo y NO es aperiodico:",
        "   contiene subgrupos no triviales pero algunas",
        "   transformaciones no son invertibles.",
        "",
        "   * Los subgrupos de M(A) son grupos finitos clasicos (vease",
        "     `invertible_elements`). Su estructura interna se estudia",
        "     en el curso de algebra como subgrupo de unidades.",
        "   * La parte 'no grupo' aparece como acciones ABSORBENTES de",
        "     algunas palabras: una vez aplicadas, no hay vuelta atras.",
    ]


def _curiosities(sheet: InfoSheet) -> List[str]:
    dfa = sheet.dfa
    info = sheet.analysis
    bullets: List[str] = []

    cota = len(dfa.states) ** len(dfa.states)
    if info.order == cota:
        bullets.append(
            f"   * M(A) ALCANZA la cota |Q|^|Q| = {cota}: las "
            "palabras inducen TODAS las funciones Q → Q posibles."
        )
    elif info.order * 4 < cota:
        bullets.append(
            f"   * M(A) es notablemente pequeno comparado con la cota "
            f"teorica |Q|^|Q| = {cota}: la dinamica del automata es muy "
            "estructurada."
        )

    if info.is_group and info.is_abelian:
        bullets.append(
            f"   * Z(M) tiene {info.center_size} elementos, igual a |M(A)|: "
            "esto es lo esperado en un grupo abeliano (todos los elementos "
            "conmutan)."
        )
    elif info.center_size > 1 and not info.is_abelian:
        bullets.append(
            f"   * El centro Z(M) tiene {info.center_size} elementos y "
            "es propio: hay simetrias internas que conmutan con todo el "
            "monoide."
        )

    if info.is_group and info.num_idempotents == 1:
        bullets.append(
            "   * El unico idempotente es la identidad: caracteristico "
            "de los grupos finitos."
        )
    elif info.num_idempotents > 1:
        bullets.append(
            f"   * Hay {info.num_idempotents} elementos idempotentes "
            "(e² = e). En un grupo solo la identidad lo es; aqui hay mas, "
            "lo que confirma que M(A) NO es grupo."
        )

    if info.is_aperiodic and not info.is_group:
        bullets.append(
            "   * M(A) es aperiodico: al iterar cualquier palabra, la "
            "transformacion inducida se estabiliza (x^k = x^(k+1)). No hay "
            "ninguna palabra que actue como una 'rotacion' ciclica."
        )

    if not bullets:
        bullets.append("   * (sin curiosidades estructurales destacables)")
    return bullets


def _recommendations(sheet: InfoSheet) -> List[str]:
    info = sheet.analysis
    recs: List[str] = []
    if info.is_group and info.is_cyclic:
        n = info.order
        w = info.cyclic_generator_word or ""
        recs.append(
            f"   * Pruebe modificar el conjunto F del AFD: con F = {{q_i}}"
            f" para distintos i obtiene los {n} lenguajes 'numero de "
            f"{w!r} ≡ i (mod {n})' y todos tienen el MISMO M(A) ≅ ℤ/{n}ℤ."
        )
        recs.append(
            "   * Genere las clases del nucleo (opcion 8 del menu o "
            "`infosheet` + busqueda manual) y verifique que coinciden con "
            "las clases de residuos."
        )
    if info.is_group and not info.is_abelian:
        recs.append(
            "   * Construya manualmente la composicion de dos palabras "
            "que no conmuten y observe la diferencia en el destino — esa "
            "es la firma del grupo no abeliano."
        )
    if info.is_aperiodic and not info.is_group:
        recs.append(
            "   * Tome una palabra cualquiera y componga f_w consigo misma "
            "varias veces: vera que a partir de cierta potencia deja de "
            "cambiar (x^k = x^(k+1)). Esa es la aperiodicidad en accion."
        )
    recs.append(
        "   * Use `python main.py verify <su_dfa>.json --regex \"...\"` "
        "para verificar que su AFD reconoce el lenguaje que cree."
    )
    recs.append(
        "   * Use la opcion 6 del menu para ver la TABLA DE CAYLEY de M(A) "
        "y la opcion 9 para exportar un reporte completo con figuras."
    )
    return recs


def _book_references(sheet: InfoSheet) -> List[str]:
    """Mapea cada concepto de la hoja a sus fuentes: el algebra a Saracino
    ("Abstract Algebra: A First Course") y la computacion a De Castro Korgi
    ("Introduccion a la Teoria de la Computacion"). El monoide de transicion
    M(A) es una construccion propia que combina ambos.
    """
    info = sheet.analysis
    out: List[str] = [
        "   El monoide de transicion M(A) es una construccion propia que",
        "   une las dos fuentes del curso:",
        "",
        "   ALGEBRA (Saracino):",
        "   §1     Operacion binaria asociativa con identidad: M(A) es un",
        "          monoide bajo la composicion de funciones.",
        "   §6     Funciones y su composicion — cada transformacion",
        "          f_w: Q -> Q y el producto f_u . f_v = f_(uv).",
        "   §2,§3  Grupos, potencias y grupos ciclicos: sustentan '¿es",
        "          grupo?', 'ciclico', el generador y la clase ℤ/nℤ.",
        "   §8,§11,§12  Relaciones de equivalencia y clases, homomorfismos",
        "          y teorema de isomorfismo: el nucleo de φ y Σ*/Ker(φ).",
        "",
        "   COMPUTACION (De Castro Korgi):",
        "   §2.3   AFD M = (Σ, Q, q0, F, δ) — la 5-tupla con la que se",
        "          construyo este monoide.",
        "   §2.7.2 Funcion de transicion extendida δ̂ — es exactamente",
        "          la formula que define cada transformacion f_w de M(A)",
        "          (f_w(q) = δ̂(q, w)).",
        "   §2.15  Teorema de Myhill-Nerode. Dos palabras son",
        "          ≡_L-equivalentes sii ningun sufijo las distingue.",
        f"          En este AFD, el nucleo de φ (de tamano {info.order}) es un",
        "          REFINAMIENTO de ≡_L; ambas coinciden si el AFD es minimo.",
        "   §2.16  Algoritmo de minimizacion. El AFD minimo es unico",
        "          (Teorema 2.15.4) y sus estados son exactamente las",
        "          clases de ≡_L; por eso M(A) es un invariante de L.",
    ]
    if info.is_group and info.is_cyclic:
        out += [
            "",
            "   La cuenta modulo n que aparece en la seccion 4 es el caso",
            "   particular en que tanto Myhill-Nerode (De Castro §2.15) como",
            f"   el nucleo de φ coinciden con la aritmetica de ℤ/{info.order}ℤ",
            "   (Saracino §3).",
        ]
    if not info.is_group and info.is_aperiodic:
        out += [
            "",
            "   La aperiodicidad (seccion 4) se define aqui con las potencias",
            "   de un elemento (Saracino §3): para todo x, x^k = x^(k+1).",
            "   Es una lectura puramente algebraica de M(A), sin salir de",
            "   las dos fuentes del curso.",
        ]
    return out


__all__ = ["InfoSheet", "build_info_sheet"]
