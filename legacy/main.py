"""
main.py
=======

Interfaz por consola del proyecto.

Funciona en dos modos:

    1. Modo interactivo (sin argumentos): muestra un menu de 10 opciones
       que cubren la totalidad del flujo del proyecto.

    2. Modo CLI directo (con subcomando), pensado para reportes en
       batch:

           python main.py report  examples/parity_dfa.json
           python main.py run     examples/parity_dfa.json 1011
           python main.py monoid  examples/parity_dfa.json
           python main.py examples

       (Si no se pasa nada se entra al menu interactivo.)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from dfa import DFA, DFAValidationError
from algebra import Homomorphism
from transition_monoid import TransitionMonoid

# Las funciones de visualizacion se importan en uso porque requieren
# librerias graficas opcionales (graphviz, matplotlib).


ROOT = Path(__file__).resolve().parent
EXAMPLES_DIR = ROOT / "examples"
OUTPUT_DIR = ROOT / "output"
EXAMPLE_FILES = {
    "1": EXAMPLES_DIR / "parity_dfa.json",
    "2": EXAMPLES_DIR / "mod3_dfa.json",
    "3": EXAMPLES_DIR / "ends_with_01_dfa.json",
}


# ----------------------------------------------------------------------
# Estado mutable del CLI interactivo
# ----------------------------------------------------------------------

class Session:
    """Mantiene el DFA, el monoide y el homomorfismo cargados."""

    def __init__(self) -> None:
        self.dfa: Optional[DFA] = None
        self.monoid: Optional[TransitionMonoid] = None
        self.hom: Optional[Homomorphism] = None

    def load(self, dfa: DFA) -> None:
        self.dfa = dfa
        self.monoid = TransitionMonoid(dfa)
        self.hom = Homomorphism(dfa, self.monoid)

    def require(self) -> tuple[DFA, TransitionMonoid, Homomorphism]:
        if self.dfa is None or self.monoid is None or self.hom is None:
            raise RuntimeError(
                "No hay un DFA cargado. Use la opcion 1 del menu."
            )
        return self.dfa, self.monoid, self.hom


# ----------------------------------------------------------------------
# Acciones del menu
# ----------------------------------------------------------------------

def action_load(session: Session) -> None:
    print("\n--- Cargar DFA ---")
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
        dfa = DFA.from_json(path)
    except (DFAValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Error al cargar el DFA: {exc}")
        return
    session.load(dfa)
    print(f"Cargado: {dfa}")


def action_show_dfa(session: Session) -> None:
    dfa, _, _ = session.require()
    print("\n--- DFA ---")
    print(f"  Nombre  : {dfa.name}")
    print(f"  Q       : {sorted(dfa.states)}")
    print(f"  Sigma   : {sorted(dfa.alphabet)}")
    print(f"  q0      : {dfa.start}")
    print(f"  F       : {sorted(dfa.accepting)}")
    print("\nTabla de transiciones:")
    print(dfa.pretty_transition_table())


def action_run_word(session: Session) -> None:
    dfa, _, _ = session.require()
    word = input("Palabra a evaluar (Enter para epsilon): ").strip()
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
        print(f"Grafo del DFA  : {png_dfa}")
    except RuntimeError as exc:
        print(f"  (omitido grafo del DFA: {exc})")
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
        dfa = DFA.from_json(path)
        session.load(dfa)
        print("=" * 60)
        print(f"Ejemplo {key}: {dfa.name}  ({path.name})")
        print("=" * 60)
        action_show_dfa(session)
        action_build_monoid(session)
        action_show_cayley(session)
        print()


# ----------------------------------------------------------------------
# Menu principal
# ----------------------------------------------------------------------

MENU = """\
============================================================
  Monoide de Transicion - Menu principal
============================================================
  1) Cargar DFA
  2) Mostrar DFA
  3) Evaluar palabra
  4) Construir monoide
  5) Mostrar transformaciones
  6) Mostrar tabla de composicion (Cayley)
  7) Mostrar nucleo (Ker phi)
  8) Mostrar clases de equivalencia
  9) Exportar reporte (texto + figuras)
 10) Ejecutar ejemplos
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
            "Herramienta para construir el monoide de transicion de un DFA "
            "y verificar el primer teorema de isomorfismo."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")

    p_report = sub.add_parser("report", help="Generar reporte completo.")
    p_report.add_argument("dfa_json")
    p_report.add_argument("--max-length", type=int, default=3)

    p_run = sub.add_parser("run", help="Ejecutar una palabra sobre el DFA.")
    p_run.add_argument("dfa_json")
    p_run.add_argument("word")

    p_monoid = sub.add_parser("monoid", help="Mostrar resumen del monoide.")
    p_monoid.add_argument("dfa_json")

    sub.add_parser("examples", help="Procesar los tres ejemplos canonicos.")

    args = parser.parse_args(argv)

    if args.cmd is None:
        interactive_menu()
        return 0

    if args.cmd == "examples":
        session = Session()
        action_run_examples(session)
        return 0

    dfa = DFA.from_json(args.dfa_json)
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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli(sys.argv[1:]))
