"""Genera las paginas HTML estaticas en web/ejemplos/ a partir de los
AFDs en examples/, ejecutando el pipeline completo del backend para
producir la hoja informativa pedagogica.

Uso:
    python scripts/build_web_examples.py

Salida:
    web/ejemplos/parity_afd.html
    web/ejemplos/mod3_afd.html
    web/ejemplos/ends_with_01_afd.html
    web/ejemplos/klein_v4_afd.html
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.language.info_sheet import build_info_sheet
from backend.models.afd import AFD


# Orden de las paginas en la barra lateral
EJEMPLOS = [
    ("parity_afd",       "Paridad de 1s"),
    ("mod3_afd",         "#1s ≡ 0 (mod 3)"),
    ("ends_with_01_afd", "Termina en 01"),
    ("klein_v4_afd",     "Klein V4"),
]


def load_afd(slug: str) -> AFD:
    path = ROOT / "examples" / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return AFD(
        states=set(data["states"]),
        alphabet=set(data["alphabet"]),
        transitions=data["transitions"],
        start=data["start"],
        accepting=set(data["accepting"]),
        name=data.get("name", slug),
    )


def render_afd_definition(afd: AFD) -> str:
    """Render textual de la 5-upla y la tabla δ."""
    sigma = sorted(afd.alphabet)
    Q = sorted(afd.states)
    F = sorted(afd.accepting)
    # Tabla δ
    head_cells = "".join(f"<th>{html.escape(s)}</th>" for s in sigma)
    body_rows = []
    for q in Q:
        cells = "".join(
            f"<td>{html.escape(afd.transitions[q][s])}</td>"
            for s in sigma
        )
        marker = ""
        if q == afd.start: marker += "→ "
        if q in afd.accepting: marker += "★ "
        body_rows.append(
            f'<tr><th>{marker}{html.escape(q)}</th>{cells}</tr>'
        )
    table_html = (
        '<table class="afd-delta">'
        f'<thead><tr><th>δ</th>{head_cells}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table>'
    )
    return f"""
<div class="afd-card">
  <h3>Definicion del AFD <span class="afd-name">{html.escape(afd.name)}</span></h3>
  <p>M = (Σ, Q, q<sub>0</sub>, F, δ) (§2.3) con:</p>
  <ul>
    <li><b>Σ</b> = {{{", ".join(f"<code>{html.escape(s)}</code>" for s in sigma)}}}</li>
    <li><b>Q</b> = {{{", ".join(f"<code>{html.escape(q)}</code>" for q in Q)}}}</li>
    <li><b>q<sub>0</sub></b> = <code>{html.escape(afd.start)}</code></li>
    <li><b>F</b> = {{{", ".join(f"<code>{html.escape(q)}</code>" for q in F)}}}</li>
  </ul>
  <p><b>Función de transición δ</b> (→ = inicial, ★ = aceptación):</p>
  {table_html}
</div>
"""


def render_sidebar(active_slug: str) -> str:
    items = []
    for slug, label in EJEMPLOS:
        cls = ' class="active"' if slug == active_slug else ""
        items.append(
            f'<a href="{slug}.html"{cls}>{html.escape(label)}</a>'
        )
    return (
        '<aside class="examples-sidebar">'
        '<h4>Hojas informativas</h4>'
        + "".join(items) +
        '</aside>'
    )


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} · syntactic-monoid</title>
<link rel="stylesheet" href="../shared/style.css">
<style>
.example-layout {{
  display: grid; grid-template-columns: 220px 1fr; gap: 2rem;
  align-items: start;
}}
@media (max-width: 900px) {{
  .example-layout {{ grid-template-columns: 1fr; }}
}}
.examples-sidebar {{
  background: #f6f8fa; border: 1px solid #d1d9e0;
  border-radius: 8px; padding: 1rem;
  position: sticky; top: 75px;
}}
.examples-sidebar h4 {{
  margin: 0 0 .6rem; font-size: .82rem; color: #57606a;
  text-transform: uppercase; letter-spacing: .04em;
}}
.examples-sidebar a {{
  display: block; padding: .35rem .6rem; border-radius: 5px;
  color: #424a53; text-decoration: none; font-size: .9rem;
  margin-bottom: .2rem;
}}
.examples-sidebar a:hover {{ background: #eaecef; }}
.examples-sidebar a.active {{ background: #ddf4ff; color: #0969da;
                              font-weight: 600; }}
.afd-card {{
  background: #f6f8fa; border: 1px solid #d1d9e0;
  border-radius: 8px; padding: 1.1rem 1.3rem; margin-bottom: 1.5rem;
}}
.afd-card h3 {{ margin-top: 0; }}
.afd-card .afd-name {{ font-family: ui-monospace, Menlo, monospace;
                       color: #0969da; }}
table.afd-delta {{ width: auto; min-width: 50%; }}
table.afd-delta th, table.afd-delta td {{
  text-align: center; font-family: ui-monospace, Menlo, monospace;
}}
.breadcrumb {{ color: #6e7681; font-size: .87rem; margin-bottom: .8rem; }}
.breadcrumb a {{ color: #6e7681; }}

/* Estilos del info-sheet renderizado */
.info-sheet h1 {{ display: none; }}    /* el h1 viene del template */
.info-sheet h2 {{ margin-top: 1.8rem; font-size: 1.25rem;
                  color: #0969da; border-bottom-color: #d1d9e0; }}
.info-sheet ul {{ padding-left: 1.4rem; }}
.info-sheet li {{ margin-bottom: .35rem; }}
.info-sheet p code, .info-sheet li code {{ font-size: .88em; }}
</style>
</head>
<body>

<nav class="site-nav">
  <a href="../index.html" class="brand">syntactic-monoid <small>ITC · Discrete Math II</small></a>
  <a href="../index.html">Inicio</a>
  <a href="../regex_visualizer.html">Regex → AFD</a>
  <a href="../mt_visualizer.html">Máquinas de Turing</a>
  <a href="parity_afd.html" class="active">Monoide</a>
  <a href="../convenciones.html">Convenciones</a>
  <span class="spacer"></span>
  <span class="ref">basado en De Castro (2024)</span>
</nav>

<main>

<p class="breadcrumb">
  <a href="../index.html">Inicio</a> ›
  Hojas informativas › <b>{name}</b>
</p>

<div class="example-layout">

  {sidebar}

  <div>
    <h1>Análisis algebraico — {name}</h1>
    <p class="lead">
      Hoja informativa pedagógica generada por el motor de
      <code>syntactic-monoid</code>: definición del AFD, monoide de
      transición <em>M(A)</em>, estructura algebraica y conexión con el
      libro de De Castro.
    </p>

    {afd_def}

    <div class="info-sheet">
      {body}
    </div>
  </div>

</div>

<footer>
  syntactic-monoid · hoja informativa generada por
  <code>scripts/build_web_examples.py</code> · regenera con
  <code>python scripts/build_web_examples.py</code>
</footer>

</main>

</body>
</html>
"""


def build_one(slug: str, label: str) -> None:
    afd = load_afd(slug)
    sheet = build_info_sheet(afd)
    md = sheet.as_markdown()
    body_html = markdown.markdown(
        md,
        extensions=["extra", "smarty"],
    )

    page_html = HTML_TEMPLATE.format(
        name=html.escape(afd.name),
        sidebar=render_sidebar(slug),
        afd_def=render_afd_definition(afd),
        body=body_html,
    )

    out_path = ROOT / "web" / "ejemplos" / f"{slug}.html"
    out_path.write_text(page_html, encoding="utf-8")
    print(f"Generado: {out_path.relative_to(ROOT)} ({len(page_html)} bytes)")


def main() -> None:
    for slug, label in EJEMPLOS:
        build_one(slug, label)


if __name__ == "__main__":
    main()
