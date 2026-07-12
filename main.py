"""
main.py
=======

Interfaz por consola del proyecto.

Funciona en dos modos:

    1. Modo interactivo (sin argumentos): muestra un menu de 10 opciones
       que cubren la totalidad del flujo del proyecto.

    2. Modo CLI directo (con subcomando), pensado para reportes en
       batch:

           python main.py report  examples/parity_afd.json
           python main.py run     examples/parity_afd.json 1011
           python main.py monoid  examples/parity_afd.json
           python main.py examples

       (Si no se pasa nada se entra al menu interactivo.)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from backend.models import AFD, AFDValidationError
from backend.algebra import Homomorphism, TransitionMonoid
from backend.language import build_info_sheet, regex_to_afd
from backend.language.regex import RegexParseError
from backend.verification import check_against_regex, verify_samples
from backend.visualization import regex_to_html

INTERACTIVE_HTML = (
    Path(__file__).resolve().parent / "web" / "index.html"
)

# Las funciones de visualizacion se importan en uso porque requieren
# librerias graficas opcionales (graphviz, matplotlib).


ROOT = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT / "examples"
OUTPUT_DIR = ROOT / "output"
EXAMPLE_FILES = {
    "1": EXAMPLES_DIR / "parity_afd.json",
    "2": EXAMPLES_DIR / "mod3_afd.json",
    "3": EXAMPLES_DIR / "ends_with_01_afd.json",
}


# ----------------------------------------------------------------------
# Estado mutable del CLI interactivo
# ----------------------------------------------------------------------

class Session:
    """Mantiene el AFD, el monoide y el homomorfismo cargados."""

    def __init__(self) -> None:
        self.dfa: Optional[AFD] = None
        self.monoid: Optional[TransitionMonoid] = None
        self.hom: Optional[Homomorphism] = None

    def load(self, dfa: AFD) -> None:
        self.dfa = dfa
        self.monoid = TransitionMonoid(dfa)
        self.hom = Homomorphism(dfa, self.monoid)

    def require(self) -> tuple[AFD, TransitionMonoid, Homomorphism]:
        if self.dfa is None or self.monoid is None or self.hom is None:
            raise RuntimeError(
                "No hay un AFD cargado. Use la opcion 1 del menu."
            )
        return self.dfa, self.monoid, self.hom


# ----------------------------------------------------------------------
# Acciones del menu
# ----------------------------------------------------------------------

def action_load(session: Session) -> None:
    print("\n--- Cargar AFD ---")
    print("Ejemplos disponibles:")
    for key, path in EXAMPLE_FILES.items():
        print(f"  {key}) {path.name}")
    print("  r) Ruta personalizada a un archivo JSON")
    choice = input("Seleccione (1/2/3/r): ").strip()
    if choice in EXAMPLE_FILES:
        path = EXAMPLE_FILES[choice]
    elif choice == "r":
        raw = input("Ruta al archivo JSON: ").strip()
        path = Path(raw).expanduser().resolve()
    else:
        print("Opcion no reconocida.")
        return
    try:
        dfa = AFD.from_json(path)
    except (AFDValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Error al cargar el AFD: {exc}")
        return
    session.load(dfa)
    print(f"Cargado: {dfa}")


def action_show_dfa(session: Session) -> None:
    dfa, _, _ = session.require()
    print("\n--- AFD ---")
    print(f"  Nombre  : {dfa.name}")
    print(f"  Q       : {sorted(dfa.states)}")
    print(f"  Sigma   : {sorted(dfa.alphabet)}")
    print(f"  q0      : {dfa.start}")
    print(f"  F       : {sorted(dfa.accepting)}")
    print("\nTabla de transiciones:")
    print(dfa.pretty_transition_table())


def action_run_word(session: Session) -> None:
    dfa, _, _ = session.require()
    word = input("Palabra a evaluar (Enter para λ): ").strip()
    try:
        final = dfa.run(word)
    except ValueError as exc:
        print(f"Error: {exc}")
        return
    accepted = dfa.accepts(word)
    print(f"  delta*({dfa.start}, {word!r}) = {final}")
    print(f"  Aceptada: {accepted}")


def action_build_monoid(session: Session) -> None:
    _, monoid, _ = session.require()
    print("\n--- Monoide de transicion M(A) ---")
    print(monoid.summary())


def action_show_transformations(session: Session) -> None:
    _, monoid, _ = session.require()
    print("\n--- Transformaciones de M(A) ---")
    for i, f in enumerate(monoid.elements):
        rep = monoid.representatives[f]
        label = "e" if rep == "" else rep
        print(f"  {i:>3}  [{label}]:")
        for line in f.two_line().splitlines():
            print(f"        {line}")


def action_show_cayley(session: Session) -> None:
    _, monoid, _ = session.require()
    print("\n--- Tabla de Cayley ---")
    print(monoid.pretty_cayley_table())


def action_show_kernel(session: Session) -> None:
    _, _, hom = session.require()
    raw = input("Longitud maxima de palabras (por defecto 3): ").strip()
    n = int(raw) if raw else 3
    print(hom.kernel_report(max_length=n))


def action_show_classes(session: Session) -> None:
    _, _, hom = session.require()
    raw = input("Longitud maxima (por defecto 3): ").strip()
    n = int(raw) if raw else 3
    print("\n--- Clases de equivalencia (cociente Sigma*/Ker phi) ---")
    for rep, f, words in hom.quotient(max_length=n):
        label = "e" if rep == "" else rep
        shown = ", ".join("e" if w == "" else w for w in words)
        print(f"  [{label}] = {{ {shown} }}")
        print(f"      f = {f}")


def action_export_report(session: Session) -> None:
    dfa, _, _ = session.require()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUTPUT_DIR / dfa.name.lower().replace(" ", "_").replace("/", "_")
    txt_path = base.with_suffix(".txt")
    from visualization import write_report

    write_report(dfa, txt_path, max_length=3)
    print(f"Reporte de texto: {txt_path}")
    try:
        from visualization import render_dfa, render_cayley_table, render_class_diagram

        png_dfa = render_dfa(dfa, base.with_name(base.name + "_dfa"))
        print(f"Grafo del AFD  : {png_dfa}")
    except RuntimeError as exc:
        print(f"  (omitido grafo del AFD: {exc})")
    try:
        from visualization import render_cayley_table, render_class_diagram

        _, monoid, hom = session.require()
        png_table = render_cayley_table(
            monoid, base.with_name(base.name + "_cayley.png")
        )
        png_classes = render_class_diagram(
            hom, base.with_name(base.name + "_classes.png"), max_length=3
        )
        print(f"Tabla Cayley   : {png_table}")
        print(f"Clases (barras): {png_classes}")
    except RuntimeError as exc:
        print(f"  (omitidas figuras: {exc})")


def action_run_examples(session: Session) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("\n--- Ejecucion de los tres ejemplos canonicos ---\n")
    for key in ("1", "2", "3"):
        path = EXAMPLE_FILES[key]
        dfa = AFD.from_json(path)
        session.load(dfa)
        print("=" * 60)
        print(f"Ejemplo {key}: {dfa.name}  ({path.name})")
        print("=" * 60)
        action_show_dfa(session)
        action_build_monoid(session)
        action_show_cayley(session)
        print()


# ----------------------------------------------------------------------
# Acciones nuevas: regex, verificacion, hoja informativa
# ----------------------------------------------------------------------

def _parse_alphabet_flag(raw: str) -> set[str]:
    """Acepta 'abc' o 'a,b,c' o 'a, b, c'. Si hay coma, divide por coma;
    si no, cada caracter es un simbolo."""
    raw = raw.strip()
    if not raw:
        return set()
    if "," in raw:
        return {token.strip() for token in raw.split(",") if token.strip()}
    return set(raw)


def action_compile_regex(session: Session) -> None:
    print("\n--- Compilar regex a AFD ---")
    pattern = input("Expresion regular: ").strip()
    if not pattern:
        print("Regex vacia, abortando.")
        return
    raw_alpha = input(
        "Alfabeto (separado por comas, o todos los caracteres juntos; "
        "Enter para inferir): "
    )
    alphabet = _parse_alphabet_flag(raw_alpha) or None
    try:
        dfa = regex_to_afd(pattern, alphabet=alphabet, name=f"L({pattern})")
    except ValueError as exc:
        print(f"Error compilando la regex: {exc}")
        return
    session.load(dfa)
    print(f"Compilado y cargado en la sesion: {dfa}")
    raw_save = input(
        "Guardar el AFD como JSON? Ruta (Enter para omitir): "
    ).strip()
    if raw_save:
        path = Path(raw_save).expanduser().resolve()
        try:
            dfa.to_json(path)
            print(f"  Guardado: {path}")
        except OSError as exc:
            print(f"  Error al guardar: {exc}")


def action_verify(session: Session) -> None:
    dfa, _, _ = session.require()
    print("\n--- Verificar el AFD contra una especificacion ---")
    print("  r) regex")
    print("  m) muestra accept/reject (archivo JSON)")
    choice = input("Modo (r/m): ").strip()
    if choice == "r":
        pattern = input("Regex esperada: ").strip()
        if not pattern:
            return
        raw_alpha = input(
            "Alfabeto (Enter usa el del AFD): "
        )
        alphabet = _parse_alphabet_flag(raw_alpha) or None
        try:
            result = check_against_regex(dfa, pattern, alphabet=alphabet)
        except ValueError as exc:
            print(f"Error: {exc}")
            return
        print(result.summary("tu AFD", f"L({pattern})"))
    elif choice == "m":
        raw = input(
            'Ruta a archivo JSON {"accept": [...], "reject": [...]}: '
        ).strip()
        if not raw:
            return
        try:
            data = json.loads(
                Path(raw).expanduser().read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error al leer la muestra: {exc}")
            return
        result = verify_samples(
            dfa, data.get("accept", []), data.get("reject", [])
        )
        print(result.summary("tu AFD"))
        if result.total > 0:
            print("\n" + result.pretty_table())
    else:
        print("Modo no reconocido.")


def action_info_sheet(session: Session) -> None:
    dfa, _, _ = session.require()
    sheet = build_info_sheet(dfa)
    print("\n" + sheet.as_text())
    raw = input("\nGuardar tambien a archivo? Ruta (.md para markdown, "
                "Enter para omitir): ").strip()
    if raw:
        path = Path(raw).expanduser().resolve()
        try:
            if path.suffix.lower() == ".md":
                sheet.write_markdown(path)
            else:
                sheet.write(path)
            print(f"  Guardado: {path}")
        except OSError as exc:
            print(f"  Error al guardar: {exc}")


def action_interactive(session: Session) -> None:
    print("\n--- Visualizador interactivo de regex (en el navegador) ---")
    if not INTERACTIVE_HTML.exists():
        print(f"  Error: no encuentro {INTERACTIVE_HTML}")
        return
    import webbrowser
    print(f"  Abriendo {INTERACTIVE_HTML.name} en el navegador por defecto...")
    print(f"  (escribe regexes en la pagina; los grafos se actualizan en vivo.)")
    try:
        webbrowser.open(INTERACTIVE_HTML.as_uri())
    except Exception as exc:
        print(f"  No se pudo abrir el navegador: {exc}")
        print(f"  Abre manualmente: {INTERACTIVE_HTML}")


def action_visualize_regex(session: Session) -> None:
    print("\n--- Visualizar regex (HTML con AFN + AFD + AFD minimo) ---")
    print("Sintaxis soportada: a, ab, a|b, a*, a+, a?, (...), [abc], [a-z], ., \\x")
    pattern = input("Expresion regular: ").strip()
    if not pattern:
        print("Regex vacia, abortando.")
        return
    raw_alpha = input(
        "Alfabeto (caracteres juntos '01' o por comas 'a,b,c'; "
        "Enter para inferir): "
    )
    alphabet = _parse_alphabet_flag(raw_alpha) or None
    raw_out = input("Ruta del HTML (Enter usa output/ por defecto): ").strip()
    out_path = Path(raw_out).expanduser().resolve() if raw_out else None
    raw_open = input("Abrir en el navegador? [S/n]: ").strip().lower()
    open_browser = raw_open != "n"
    try:
        path = regex_to_html(
            pattern,
            alphabet=alphabet,
            output_path=out_path,
            open_browser=open_browser,
        )
    except (RegexParseError, ValueError) as exc:
        print(f"Error al compilar la regex: {exc}")
        return
    print(f"  HTML generado: {path}")
    if open_browser:
        print("  (abierto en el navegador por defecto)")


# ----------------------------------------------------------------------
# Menu principal
# ----------------------------------------------------------------------

MENU = """\
============================================================
  Monoide de Transicion - Menu principal
============================================================
  1) Cargar AFD
  2) Mostrar AFD
  3) Evaluar palabra
  4) Construir monoide
  5) Mostrar transformaciones
  6) Mostrar tabla de composicion (Cayley)
  7) Mostrar nucleo (Ker phi)
  8) Mostrar clases de equivalencia
  9) Exportar reporte (texto + figuras)
 10) Ejecutar ejemplos
 11) Compilar regex a AFD
 12) Verificar AFD contra regex o muestra
 13) Generar hoja informativa (algebra + automatas)
 14) Visualizar regex en HTML estatico (AFN + AFD + AFD minimo)
 15) ABRIR visualizador interactivo en el navegador (live, sin terminal)
  0) Salir
"""

ACTIONS = {
    "1": action_load,
    "2": action_show_dfa,
    "3": action_run_word,
    "4": action_build_monoid,
    "5": action_show_transformations,
    "6": action_show_cayley,
    "7": action_show_kernel,
    "8": action_show_classes,
    "9": action_export_report,
    "10": action_run_examples,
    "11": action_compile_regex,
    "12": action_verify,
    "13": action_info_sheet,
    "14": action_visualize_regex,
    "15": action_interactive,
}


def interactive_menu() -> None:
    session = Session()
    while True:
        print(MENU)
        choice = input("Opcion: ").strip()
        if choice == "0":
            print("Hasta luego.")
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("Opcion no reconocida.")
            continue
        try:
            action(session)
        except RuntimeError as exc:
            print(f"Error: {exc}")
        except KeyboardInterrupt:
            print("\n(operacion interrumpida)")


# ----------------------------------------------------------------------
# CLI directa con argparse
# ----------------------------------------------------------------------

def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="syntactic-monoid",
        description=(
            "Herramienta para construir, verificar y analizar algebraicamente "
            "automatas finitos: lenguajes regulares, monoide de transicion, "
            "primer teorema del isomorfismo y conexion con teoria de grupos."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")

    p_report = sub.add_parser("report", help="Generar reporte completo.")
    p_report.add_argument("dfa_json")
    p_report.add_argument("--max-length", type=int, default=3)

    p_run = sub.add_parser("run", help="Ejecutar una palabra sobre el AFD.")
    p_run.add_argument("dfa_json")
    p_run.add_argument("word")

    p_monoid = sub.add_parser("monoid", help="Mostrar resumen del monoide.")
    p_monoid.add_argument("dfa_json")

    sub.add_parser("examples", help="Procesar los tres ejemplos canonicos.")

    p_compile = sub.add_parser(
        "from-regex",
        help="Compilar una regex a AFD (Thompson + subset construction).",
    )
    p_compile.add_argument("pattern", help="Expresion regular.")
    p_compile.add_argument(
        "--alphabet",
        default=None,
        help="Alfabeto: caracteres juntos ('01') o lista por comas ('a,b').",
    )
    p_compile.add_argument(
        "--out",
        default=None,
        help="Ruta JSON donde guardar el AFD resultante.",
    )

    p_verify = sub.add_parser(
        "verify",
        help="Verificar un AFD contra una regex y/o una muestra accept/reject.",
    )
    p_verify.add_argument("dfa_json")
    p_verify.add_argument(
        "--regex",
        default=None,
        help="Regex esperada para comparar por equivalencia.",
    )
    p_verify.add_argument(
        "--samples",
        default=None,
        help='Archivo JSON con {"accept": [...], "reject": [...]}.',
    )
    p_verify.add_argument(
        "--alphabet",
        default=None,
        help="Alfabeto explicito para la regex (si difiere del AFD).",
    )

    p_info = sub.add_parser(
        "infosheet",
        help="Generar la hoja informativa pedagogica del AFD.",
    )
    p_info.add_argument("dfa_json")
    p_info.add_argument("--out", default=None, help="Ruta de salida.")
    p_info.add_argument(
        "--markdown",
        action="store_true",
        help="Usar formato Markdown en lugar de texto plano.",
    )

    p_visual = sub.add_parser(
        "visualize",
        help="Generar pagina HTML autocontenida con AFN + AFD + AFD minimo "
             "de una regex.",
    )
    p_visual.add_argument("pattern", help="Expresion regular a visualizar.")
    p_visual.add_argument(
        "--alphabet",
        default=None,
        help="Alfabeto: caracteres juntos ('01') o lista por comas ('a,b').",
    )
    p_visual.add_argument(
        "--out",
        default=None,
        help="Ruta del archivo HTML resultante.",
    )
    p_visual.add_argument(
        "--no-open",
        action="store_true",
        help="No abrir automaticamente el HTML en el navegador.",
    )

    sub.add_parser(
        "interactive",
        help="Abrir el visualizador interactivo en el navegador "
             "(typing -> grafo en vivo, todo del lado del cliente).",
    )

    args = parser.parse_args(argv)

    if args.cmd is None:
        interactive_menu()
        return 0

    if args.cmd == "examples":
        session = Session()
        action_run_examples(session)
        return 0

    if args.cmd == "from-regex":
        return _cli_from_regex(args)

    if args.cmd == "verify":
        return _cli_verify(args)

    if args.cmd == "infosheet":
        return _cli_infosheet(args)

    if args.cmd == "visualize":
        return _cli_visualize(args)

    if args.cmd == "interactive":
        return _cli_interactive()

    # A partir de aqui los subcomandos requieren cargar el AFD.
    dfa = AFD.from_json(args.dfa_json)
    session = Session()
    session.load(dfa)

    if args.cmd == "report":
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        from visualization import write_report

        out = write_report(dfa, OUTPUT_DIR / f"{Path(args.dfa_json).stem}.txt",
                           max_length=args.max_length)
        print(f"Reporte generado: {out}")
    elif args.cmd == "run":
        final = dfa.run(args.word)
        print(f"  delta*({dfa.start}, {args.word!r}) = {final}")
        print(f"  Aceptada: {dfa.accepts(args.word)}")
    elif args.cmd == "monoid":
        monoid = session.monoid
        assert monoid is not None
        print(monoid.summary())
        print()
        print(monoid.pretty_cayley_table())
    return 0


# ----------------------------------------------------------------------
# Subcomandos nuevos (logica de la CLI directa)
# ----------------------------------------------------------------------

def _cli_from_regex(args: argparse.Namespace) -> int:
    alphabet = _parse_alphabet_flag(args.alphabet) if args.alphabet else None
    try:
        dfa = regex_to_afd(
            args.pattern, alphabet=alphabet, name=f"L({args.pattern})"
        )
    except ValueError as exc:
        print(f"Error compilando la regex: {exc}", file=sys.stderr)
        return 1
    print(dfa)
    print(dfa.pretty_transition_table())
    if args.out:
        path = Path(args.out).expanduser().resolve()
        dfa.to_json(path)
        print(f"AFD guardado en: {path}")
    return 0


def _cli_verify(args: argparse.Namespace) -> int:
    dfa = AFD.from_json(args.dfa_json)
    if args.regex is None and args.samples is None:
        print(
            "Debe especificar al menos --regex o --samples.", file=sys.stderr
        )
        return 1
    failed = False
    if args.regex is not None:
        alphabet = (
            _parse_alphabet_flag(args.alphabet) if args.alphabet else None
        )
        try:
            result = check_against_regex(dfa, args.regex, alphabet=alphabet)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(result.summary("tu AFD", f"L({args.regex})"))
        if not result.equivalent:
            failed = True
    if args.samples is not None:
        try:
            data = json.loads(
                Path(args.samples).expanduser().read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error al leer la muestra: {exc}", file=sys.stderr)
            return 1
        result = verify_samples(
            dfa, data.get("accept", []), data.get("reject", [])
        )
        print(result.summary("tu AFD"))
        if result.total > 0:
            print("\n" + result.pretty_table())
        if not result.all_pass:
            failed = True
    return 1 if failed else 0


def _cli_infosheet(args: argparse.Namespace) -> int:
    dfa = AFD.from_json(args.dfa_json)
    sheet = build_info_sheet(dfa)
    text = sheet.as_markdown() if args.markdown else sheet.as_text()
    print(text)
    if args.out:
        path = Path(args.out).expanduser().resolve()
        if args.markdown:
            sheet.write_markdown(path)
        else:
            sheet.write(path)
        print(f"\nGuardado en: {path}", file=sys.stderr)
    return 0


def _cli_interactive() -> int:
    """Abre web/index.html en el navegador por defecto."""
    if not INTERACTIVE_HTML.exists():
        print(
            f"Error: no encuentro {INTERACTIVE_HTML}", file=sys.stderr
        )
        return 1
    import webbrowser
    print(f"Abriendo {INTERACTIVE_HTML} en el navegador...")
    try:
        webbrowser.open(INTERACTIVE_HTML.as_uri())
    except Exception as exc:
        print(f"No se pudo abrir el navegador: {exc}", file=sys.stderr)
        print(f"Abre manualmente: {INTERACTIVE_HTML}")
        return 1
    return 0


def _cli_visualize(args: argparse.Namespace) -> int:
    alphabet = _parse_alphabet_flag(args.alphabet) if args.alphabet else None
    out_path = Path(args.out).expanduser().resolve() if args.out else None
    try:
        path = regex_to_html(
            args.pattern,
            alphabet=alphabet,
            output_path=out_path,
            open_browser=not args.no_open,
        )
    except (RegexParseError, ValueError) as exc:
        print(f"Error al compilar la regex: {exc}", file=sys.stderr)
        return 1
    print(f"HTML generado: {path}")
    if not args.no_open:
        print("(abierto en el navegador por defecto)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli(sys.argv[1:]))
