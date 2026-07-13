"""
backend.visualization.regex_view
================================

Visualizacion de expresiones regulares como pagina HTML autocontenida.

Pipeline:

    pattern  --(parser + construccion AFN-λ)-->  λ-AFN
                                        |
                                        v  subset construction
                                       AFD
                                        |
                                        v  minimizacion
                                       AFD minimo

Cada autómata se renderiza como SVG mediante Graphviz y se incrusta
directamente en una pagina HTML que ademas incluye:

    * la regex original y el alfabeto inferido / suministrado,
    * una hoja de sintaxis en castellano con todos los operadores,
    * estadisticas (numero de estados, numero de aristas) por grafo,
    * el codigo DOT plegable bajo `<details>`, para que el alumno
      pueda exportar el grafico a otras herramientas.

El archivo resultante es UN SOLO HTML que se puede compartir, abrir
sin conexion y enviar por correo.
"""

from __future__ import annotations

import html as _html
import re
import urllib.parse as _urllib
import webbrowser
from pathlib import Path
from typing import Iterable, Optional, Tuple

from backend.language.regex import RegexParseError, regex_to_afn
from backend.models.afd import AFD
from backend.models.afn import AFN


# ----------------------------------------------------------------------
# API publica
# ----------------------------------------------------------------------

def regex_to_html(
    pattern: str,
    alphabet: Optional[Iterable[str]] = None,
    output_path: Optional[Path] = None,
    open_browser: bool = False,
) -> Path:
    """Compila `pattern` y produce una pagina HTML con los tres digrafos.

    Parametros
    ----------
    pattern : str
        Expresion regular en la sintaxis del proyecto.
    alphabet : Iterable[str], opcional
        Alfabeto explicito. Si es None, se infiere de los literales.
    output_path : Path, opcional
        Ruta del HTML resultante. Por defecto
        `output/regex_<slug>.html` en el directorio del proyecto.
    open_browser : bool
        Si es True, abre el archivo en el navegador por defecto del SO.

    Devuelve
    --------
    Path : ruta absoluta al HTML generado.

    Excepciones
    -----------
    RegexParseError : si la regex no es valida; el llamador puede
                      capturarlo y mostrar el mensaje al usuario.
    """
    try:
        afn = regex_to_afn(pattern, alphabet=alphabet)
    except RegexParseError:
        raise
    dfa = afn.to_afd()
    minimal = dfa.minimize()

    nfa_dot = _nfa_to_dot(afn)
    dfa_dot = _dfa_to_dot(dfa)
    min_dot = _dfa_to_dot(minimal)

    nfa_svg = _render_svg(nfa_dot)
    dfa_svg = _render_svg(dfa_dot)
    min_svg = _render_svg(min_dot)

    html = _render_html_page(
        pattern=pattern,
        alphabet=sorted(afn.alphabet),
        afn=afn,
        dfa=dfa,
        minimal=minimal,
        nfa_svg=nfa_svg,
        dfa_svg=dfa_svg,
        min_svg=min_svg,
        nfa_dot=nfa_dot,
        dfa_dot=dfa_dot,
        min_dot=min_dot,
    )

    if output_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        output_path = project_root / "output" / f"regex_{_slug(pattern)}.html"
    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    if open_browser:
        try:
            webbrowser.open(output_path.as_uri())
        except Exception:  # navegador no disponible (CI, contenedor)
            pass

    return output_path


# ----------------------------------------------------------------------
# DOT
# ----------------------------------------------------------------------

def _dot_id(name: str) -> str:
    """Cadena valida como identificador DOT (entre comillas, con escapes)."""
    safe = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{safe}"'


def _nfa_to_dot(afn: AFN) -> str:
    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  fontname="Helvetica";',
        '  node [fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=10];',
        '  __start__ [shape=none, label="", width=0, height=0];',
    ]
    for q in sorted(afn.states):
        shape = "doublecircle" if q in afn.accepting else "circle"
        lines.append(f"  {_dot_id(q)} [shape={shape}];")
    lines.append(f"  __start__ -> {_dot_id(afn.start)};")
    # Aristas con simbolos (agrupar a, b sobre misma arista)
    for q in sorted(afn.states):
        bucket: dict[str, list[str]] = {}
        for a in sorted(afn.alphabet):
            for t in sorted(afn.transitions.get(q, {}).get(a, set())):
                bucket.setdefault(t, []).append(a)
        for t, syms in bucket.items():
            label = ",".join(syms)
            lines.append(
                f"  {_dot_id(q)} -> {_dot_id(t)} [label={_dot_id(label)}];"
            )
        # λ-transiciones (linea discontinua gris)
        for t in sorted(afn.lambda_transitions.get(q, set())):
            lines.append(
                f'  {_dot_id(q)} -> {_dot_id(t)} '
                f'[label="λ", style="dashed", color="#888888", fontcolor="#666666"];'
            )
    lines.append("}")
    return "\n".join(lines)


def _dfa_to_dot(dfa: AFD) -> str:
    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  fontname="Helvetica";',
        '  node [fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=10];',
        '  __start__ [shape=none, label="", width=0, height=0];',
    ]
    for q in sorted(dfa.states):
        shape = "doublecircle" if q in dfa.accepting else "circle"
        lines.append(f"  {_dot_id(q)} [shape={shape}];")
    lines.append(f"  __start__ -> {_dot_id(dfa.start)};")
    for q in sorted(dfa.states):
        bucket: dict[str, list[str]] = {}
        for a in sorted(dfa.alphabet):
            target = dfa.transitions[q][a]
            bucket.setdefault(target, []).append(a)
        for t, syms in bucket.items():
            label = ",".join(syms)
            lines.append(
                f"  {_dot_id(q)} -> {_dot_id(t)} [label={_dot_id(label)}];"
            )
    lines.append("}")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# SVG: Graphviz con fallback si no esta disponible
# ----------------------------------------------------------------------

def _render_svg(dot: str) -> str:
    """Devuelve markup SVG renderizado por Graphviz, o un bloque HTML
    de fallback si Graphviz no esta instalado."""
    try:
        import graphviz  # type: ignore
    except ImportError:
        return _dot_fallback_block(
            dot,
            "El paquete Python `graphviz` no esta instalado. "
            "Ejecute `pip install graphviz` (y el binario del sistema).",
        )
    try:
        source = graphviz.Source(dot, format="svg")
        svg_bytes = source.pipe()
    except Exception as exc:  # ExecutableNotFound, CalledProcessError, ...
        return _dot_fallback_block(
            dot,
            f"No se pudo ejecutar Graphviz: {exc}. "
            "Verifique que el binario `dot` este en PATH.",
        )
    svg = svg_bytes.decode("utf-8")
    # Quitar el prologo XML y el DOCTYPE para incrustar en HTML.
    start = svg.find("<svg")
    if start > 0:
        svg = svg[start:]
    return svg


def _dot_fallback_block(dot: str, message: str) -> str:
    safe_dot = _html.escape(dot)
    online_url = (
        "https://dreampuf.github.io/GraphvizOnline/#"
        + _urllib.quote(dot)
    )
    return f"""
<div class="dot-fallback">
  <p><strong>No se pudo renderizar el grafo:</strong> {_html.escape(message)}</p>
  <p>Puede pegar el codigo DOT que sigue en
     <a href="{online_url}" target="_blank" rel="noopener">Graphviz Online</a>
     o instalar Graphviz localmente.</p>
  <pre>{safe_dot}</pre>
</div>
""".strip()


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               'Helvetica Neue', Arial, sans-serif;
  max-width: 1100px; margin: 0 auto; padding: 1.5rem 2rem;
  line-height: 1.55; color: #1f2328; background: #fff;
}
h1 { font-size: 1.7rem; margin: 0 0 .8rem 0; }
h2 { font-size: 1.18rem; margin: 2.4rem 0 .6rem;
     padding-bottom: .35rem; border-bottom: 2px solid #eaecef; }
header .pattern {
  font-size: 1.25rem; background: #f6f8fa; padding: .75rem 1rem;
  border-radius: 8px; border: 1px solid #d0d7de;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-all;
}
header .alphabet { color: #57606a; font-size: .94rem; margin-top: .55rem; }
code {
  background: #f0f3f6; padding: 1px 5px; border-radius: 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .9em;
}
.syntax table { border-collapse: collapse; width: 100%; font-size: .95rem; }
.syntax th { text-align: left; background: #f0f3f6;
             padding: .5rem .75rem; font-weight: 600; }
.syntax td { border-top: 1px solid #eaecef; padding: .5rem .75rem;
             vertical-align: top; }
.syntax td:first-child { width: 9rem; }
.note {
  background: #fff8e1; border-left: 4px solid #ffca28;
  padding: .7rem 1rem; border-radius: 4px; margin: 1rem 0;
  font-size: .92rem;
}
.svg-wrap {
  overflow-x: auto; padding: 1rem; background: #fbfbfd;
  border-radius: 8px; border: 1px solid #eaecef;
  display: flex; justify-content: center;
}
.svg-wrap svg { max-width: 100%; height: auto; }
.stat { color: #57606a; font-size: .92rem; margin: .4rem 0 1rem 0; }
.stat strong { color: #1f2328; }
details { margin-top: .8rem; }
details summary { cursor: pointer; color: #57606a; font-size: .87rem;
                  user-select: none; }
details summary:hover { color: #0969da; }
details pre {
  background: #f5f5f7; padding: .8rem 1rem; border-radius: 4px;
  overflow-x: auto; font-size: .8rem; line-height: 1.4;
  margin-top: .4rem; font-family: ui-monospace, SFMono-Regular, Menlo,
                                   Consolas, monospace;
}
footer { color: #6e7681; font-size: .85rem; margin-top: 3.5rem;
         border-top: 1px solid #eaecef; padding-top: 1rem; text-align: center; }
.dot-fallback {
  background: #fff3cd; border: 1px solid #ffe082;
  padding: 1rem 1.2rem; border-radius: 6px;
}
.dot-fallback pre { background: #fff; }
""".strip()


_SYNTAX_HELP = """
<h2>Como escribir tu regex</h2>
<table>
  <thead>
    <tr><th>Sintaxis</th><th>Significado</th><th>Ejemplo</th></tr>
  </thead>
  <tbody>
    <tr><td><code>a</code></td>
        <td>simbolo literal <code>a</code></td>
        <td><code>0</code> reconoce solo <code>"0"</code></td></tr>
    <tr><td><code>ab</code></td>
        <td>concatenacion: <code>a</code> seguido de <code>b</code></td>
        <td><code>01</code> reconoce solo <code>"01"</code></td></tr>
    <tr><td><code>a|b</code></td>
        <td>alternativa: <code>a</code> o <code>b</code></td>
        <td><code>0|1</code> reconoce <code>"0"</code> o <code>"1"</code></td></tr>
    <tr><td><code>a*</code></td>
        <td>cero o mas <code>a</code>'s (estrella de Kleene)</td>
        <td><code>0*</code> reconoce <code>""</code>, <code>"0"</code>, <code>"00"</code>, ...</td></tr>
    <tr><td><code>a+</code></td>
        <td>una o mas <code>a</code>'s</td>
        <td><code>1+</code> reconoce <code>"1"</code>, <code>"11"</code>, ...</td></tr>
    <tr><td><code>a?</code></td>
        <td>cero o una <code>a</code></td>
        <td><code>0?1</code> reconoce <code>"1"</code> o <code>"01"</code></td></tr>
    <tr><td><code>(...)</code></td>
        <td>agrupacion</td>
        <td><code>(01)*</code> reconoce <code>""</code>, <code>"01"</code>, <code>"0101"</code>, ...</td></tr>
    <tr><td><code>[abc]</code></td>
        <td>cualquier simbolo de la clase</td>
        <td><code>[01]+</code> = cualquier cadena binaria no vacia</td></tr>
    <tr><td><code>[a-z]</code></td>
        <td>rango de simbolos</td>
        <td><code>[a-c]</code> = <code>a</code>, <code>b</code> o <code>c</code></td></tr>
    <tr><td><code>.</code></td>
        <td>cualquier simbolo del alfabeto</td>
        <td><code>.*01</code> = cualquier cosa terminada en <code>01</code></td></tr>
    <tr><td><code>\\x</code></td>
        <td>simbolo literal <code>x</code> (escape)</td>
        <td><code>\\*</code> = el caracter <code>*</code></td></tr>
  </tbody>
</table>
<p class="note">
  <strong>Precedencia (de menor a mayor):</strong>
  union <code>|</code> &lt; concatenacion &lt; repeticion <code>* + ?</code>.
  Use parentesis para forzar otro agrupamiento:
  <code>(0|1)*</code> &ne; <code>0|1*</code>.
</p>
<p class="note">
  <strong>Alfabeto:</strong> si no lo especifica con <code>--alphabet</code>
  se infiere de los literales que aparecen en la regex. Para usar
  <code>.</code> con simbolos que no aparecen literalmente, suministre
  un alfabeto explicito (p. ej. <code>--alphabet 01</code>).
</p>
<p class="note">
  <strong>Importante:</strong> una expresion regular SOLO describe
  lenguajes regulares. Lenguajes como <code>a<sup>n</sup>b<sup>n</sup></code>
  no son regulares y no pueden expresarse con esta sintaxis: requieren
  un automata de pila (PDA) o una maquina de Turing.
</p>
""".strip()


def _slug(s: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return safe[:40] or "regex"


def _edge_count_nfa(afn: AFN) -> int:
    n = 0
    for q in afn.states:
        for a in afn.alphabet:
            n += len(afn.transitions.get(q, {}).get(a, set()))
        n += len(afn.lambda_transitions.get(q, set()))
    return n


def _edge_count_dfa(dfa: AFD) -> int:
    return len(dfa.states) * len(dfa.alphabet)


def _reduction_note(original: int, minimized: int) -> str:
    if minimized == original:
        return " (el AFD por subconjuntos ya era minimo)"
    return f" (reduccion: {original} → {minimized})"


def _render_html_page(
    *,
    pattern: str,
    alphabet: list[str],
    afn: AFN,
    dfa: AFD,
    minimal: AFD,
    nfa_svg: str,
    dfa_svg: str,
    min_svg: str,
    nfa_dot: str,
    dfa_dot: str,
    min_dot: str,
) -> str:
    nfa_states, nfa_edges = len(afn.states), _edge_count_nfa(afn)
    dfa_states, dfa_edges = len(dfa.states), _edge_count_dfa(dfa)
    min_states, min_edges = len(minimal.states), _edge_count_dfa(minimal)
    title = f"Visualizacion: {pattern}"
    safe_pattern = _html.escape(pattern)
    safe_alpha = ", ".join(_html.escape(a) for a in alphabet)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_html.escape(title)}</title>
  <style>{_CSS}</style>
</head>
<body>
  <header>
    <h1>Visualizacion de expresion regular</h1>
    <div class="pattern">{safe_pattern}</div>
    <p class="alphabet">Alfabeto inferido &Sigma; = {{{safe_alpha}}}</p>
  </header>

  <section class="syntax">
    {_SYNTAX_HELP}
  </section>

  <section class="diagram">
    <h2>1. AFN-λ por construccion clasica</h2>
    <p class="stat">
      Cada operador de la regex genera un fragmento de AFN con sus
      &λ;-transiciones (lineas discontinuas grises).
      <strong>{nfa_states} estados</strong>,
      <strong>{nfa_edges} transiciones</strong>.
    </p>
    <div class="svg-wrap">{nfa_svg}</div>
    <details>
      <summary>Ver codigo DOT</summary>
      <pre>{_html.escape(nfa_dot)}</pre>
    </details>
  </section>

  <section class="diagram">
    <h2>2. AFD por construccion de subconjuntos</h2>
    <p class="stat">
      Cada estado del AFD es un conjunto de estados del AFN (cerradura
      &λ;).
      <strong>{dfa_states} estados</strong>,
      <strong>{dfa_edges} transiciones</strong>.
    </p>
    <div class="svg-wrap">{dfa_svg}</div>
    <details>
      <summary>Ver codigo DOT</summary>
      <pre>{_html.escape(dfa_dot)}</pre>
    </details>
  </section>

  <section class="diagram">
    <h2>3. AFD minimo (minimizacion, §2.16)</h2>
    <p class="stat">
      El AFD con la cantidad minima de estados que reconoce el mismo
      lenguaje. Es unico salvo renombramiento.
      <strong>{min_states} estados</strong>,
      <strong>{min_edges} transiciones</strong>{_reduction_note(dfa_states, min_states)}.
    </p>
    <div class="svg-wrap">{min_svg}</div>
    <details>
      <summary>Ver codigo DOT</summary>
      <pre>{_html.escape(min_dot)}</pre>
    </details>
  </section>

  <footer>
    Generado por <code>syntactic-monoid</code> &middot;
    cierra y reabre con otra regex desde
    <code>python main.py visualize "&lt;regex&gt;"</code> o desde la
    opcion 14 del menu interactivo.
  </footer>
</body>
</html>
"""
