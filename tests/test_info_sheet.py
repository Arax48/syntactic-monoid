"""Pruebas para backend.language.info_sheet.

No comprobamos texto literal (el formato puede cambiar). Comprobamos
INVARIANTES de contenido: el numero correcto de secciones, que la
identificacion del grupo aparezca cuando deba, que la explicacion
algebraica sea la apropiada a la estructura, etc.
"""

from __future__ import annotations

from backend.language.info_sheet import InfoSheet, build_info_sheet
from backend.models import AFD


# ----------------------------------------------------------------------
# Construccion
# ----------------------------------------------------------------------

def test_build_info_sheet_acepta_dfa(parity_dfa: AFD) -> None:
    sheet = build_info_sheet(parity_dfa)
    assert isinstance(sheet, InfoSheet)
    assert sheet.dfa is parity_dfa
    assert sheet.analysis.is_group
    assert sheet.analysis.isomorphic_to == "ℤ/2ℤ"


def test_as_text_contiene_las_seis_secciones(parity_dfa: AFD) -> None:
    sheet = build_info_sheet(parity_dfa)
    text = sheet.as_text()
    for header in (
        "TU AUTOMATA",
        "MONOIDE SINTACTICO",
        "¿ES UN GRUPO?",
        "CONEXIONES CON DISCRETE MATH",
        "CURIOSIDADES",
        "¿Y AHORA QUE?",
    ):
        assert header in text, f"falta seccion: {header!r}"


# ----------------------------------------------------------------------
# Texto - contenido por tipo de monoide
# ----------------------------------------------------------------------

def test_grupo_ciclico_menciona_aritmetica_modular(parity_dfa: AFD) -> None:
    sheet = build_info_sheet(parity_dfa)
    text = sheet.as_text()
    # Para Z/2Z debe mencionar que es ciclico, su grupo y la conexion
    # con clases modulares.
    assert "ℤ/2ℤ" in text
    assert "ciclico" in text.lower() or "cíclico" in text.lower()
    assert "modul" in text.lower()  # "modulo" o "modular"


def test_mod3_menciona_clases_modulo_3(mod3_dfa: AFD) -> None:
    sheet = build_info_sheet(mod3_dfa)
    text = sheet.as_text()
    assert "ℤ/3ℤ" in text
    # Tiene que aparecer una referencia explicita a las clases de
    # residuos modulo 3.
    assert "modulo 3" in text.lower() or "modulo 3" in text.lower()


def test_no_grupo_aperiodico_menciona_schutzenberger(ends_01_dfa: AFD) -> None:
    sheet = build_info_sheet(ends_01_dfa)
    text = sheet.as_text()
    assert "NO es un grupo" in text or "NO - existen" in text
    # ends_with_01 es aperiodico -> debe mencionar Schutzenberger y star-free.
    assert "Schutzenberger" in text or "star-free" in text or "STAR-FREE" in text


def test_no_grupo_no_aperiodico_caso_por_defecto() -> None:
    """Construye un AFD cuyo M(A) es no-grupo pero no aperiodico.

    Truco: un AFD en el que algun simbolo permute un sub-grupo de
    estados y otro absorba. Por ejemplo, alfabeto {a, b} sobre tres
    estados {p, q, r} con `a` permutando p<->q y `b` colapsando todo a r.
    """
    dfa = AFD(
        states={"p", "q", "r"},
        alphabet={"a", "b"},
        transitions={
            "p": {"a": "q", "b": "r"},
            "q": {"a": "p", "b": "r"},
            "r": {"a": "r", "b": "r"},
        },
        start="p",
        accepting={"p"},
        name="grupo_y_absorbente",
    )
    sheet = build_info_sheet(dfa)
    text = sheet.as_text()
    # M(A) tiene subgrupo Z/2 (de las permutaciones de p,q via 'a') pero
    # NO es aperiodico, y NO es un grupo.
    assert not sheet.analysis.is_group
    assert not sheet.analysis.is_aperiodic
    # Debe aparecer el bloque "por defecto" o el bloque general:
    assert "subgrupo" in text.lower() or "absorbent" in text.lower()


# ----------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------

def test_markdown_usa_encabezados(mod3_dfa: AFD) -> None:
    md = build_info_sheet(mod3_dfa).as_markdown()
    assert md.startswith("# Hoja informativa")
    # Las 6 secciones aparecen como ## ...
    for header in (
        "## 1. Tu autómata",
        "## 2. Monoide sintáctico",
        "## 3. ¿Es un grupo?",
        "## 4. Conexiones",
        "## 5. Curiosidades",
        "## 6. ¿Y ahora qué?",
    ):
        assert header in md, f"falta encabezado: {header!r}"


# ----------------------------------------------------------------------
# Escritura a disco
# ----------------------------------------------------------------------

def test_write_y_write_markdown_crean_archivos(
    parity_dfa: AFD, tmp_path
) -> None:
    sheet = build_info_sheet(parity_dfa)
    txt = sheet.write(tmp_path / "hoja.txt")
    md = sheet.write_markdown(tmp_path / "hoja.md")
    assert txt.exists() and txt.read_text(encoding="utf-8").startswith("=")
    assert md.exists() and md.read_text(encoding="utf-8").startswith("# ")
