# Estudio Algebraico de DFAs vía Monoides de Transición

Implementación matemáticamente rigurosa y completa en Python para construir
el **monoide de transición** `M(A)` asociado a un Autómata Finito Determinista,
verificar el **homomorfismo natural** `φ : Σ* → M(A)`, calcular su **núcleo**
y comprobar el **Primer Teorema de Isomorfismo** sobre monoides:

```
Σ* / Ker(φ)  ≅  Im(φ) = M(A)
```

Proyecto integrador de **Matemática Discreta II** y **Teoría de la Computación**.

---

## 1. Estructura del proyecto

```
syntactic-monoid/
├── main.py                  # CLI interactiva + subcomandos
├── dfa.py                   # Clase DFA y δ*
├── transformation.py        # Clase Transformation (f : Q→Q)
├── transition_monoid.py     # Clase TransitionMonoid (BFS, Cayley)
├── algebra.py               # Clase Homomorphism (φ, ker, cociente)
├── visualization.py         # Graphviz + matplotlib + reportes
├── examples/                # DFAs de ejemplo en JSON
│   ├── parity_dfa.json
│   ├── mod3_dfa.json
│   └── ends_with_01_dfa.json
├── tests/                   # Suite pytest (≥ 51 pruebas)
│   ├── conftest.py
│   ├── test_dfa.py
│   ├── test_transformation.py
│   ├── test_transition_monoid.py
│   └── test_algebra.py
├── docs/
│   ├── report.md            # Informe académico (13 secciones)
│   └── presentation.md      # Presentación (≥ 15 diapositivas)
├── output/                  # Reportes y figuras generadas (creado en runtime)
├── requirements.txt
└── README.md
```

## 2. Instalación

Se recomienda Python 3.10+ y un entorno virtual.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> `graphviz` requiere además el binario del sistema (`dot`). En Fedora:
> `sudo dnf install graphviz`. En Debian/Ubuntu: `sudo apt install graphviz`.

## 3. Ejecución rápida

### Modo interactivo (menú de 10 opciones)

```bash
python main.py
```

Opciones:
1. Cargar DFA
2. Mostrar DFA
3. Evaluar palabra
4. Construir monoide
5. Mostrar transformaciones
6. Mostrar tabla de composición (Cayley)
7. Mostrar núcleo (Ker φ)
8. Mostrar clases de equivalencia
9. Exportar reporte (texto + figuras)
10. Ejecutar ejemplos canónicos

### Subcomandos directos

```bash
# Resumen + tabla de Cayley
python main.py monoid  examples/parity_dfa.json

# Evaluar una palabra
python main.py run     examples/mod3_dfa.json 110011

# Generar reporte completo
python main.py report  examples/ends_with_01_dfa.json

# Ejecutar los tres ejemplos canónicos
python main.py examples
```

## 4. Suite de pruebas

```bash
pytest tests/ -v
```

51 pruebas que cubren validación estructural del DFA, recursión de `δ*`,
álgebra de transformaciones (asociatividad, identidad, hashing), construcción
del monoide (cerradura, cota `|Q|^|Q|`, tabla de Cayley) y propiedades de `φ`
(homomorfismo, reflexividad/simetría/transitividad de `∼`, Primer Teorema
del Isomorfismo).

## 5. Ejemplos incluidos

| Ejemplo | `\|Q\|` | Lenguaje | `\|M(A)\|` | ¿Grupo? | Estructura |
|--------|---|---|---|---|---|
| `parity_dfa.json` | 2 | nº par de 1s | 2 | sí | ≅ ℤ/2ℤ |
| `mod3_dfa.json`   | 3 | nº de 1s ≡ 0 (mód 3) | 3 | sí | ≅ ℤ/3ℤ |
| `ends_with_01_dfa.json` | 3 | termina en 01 | 5 | no | monoide aperiódico |

## 6. Documentación

- **Informe académico completo:** [`docs/report.md`](docs/report.md) — 13
  secciones (resumen, marco teórico, fundamentación matemática, metodología,
  ejemplos, resultados, discusión, conclusiones, referencias).
- **Presentación:** [`docs/presentation.md`](docs/presentation.md) — 16
  diapositivas listas para defensa.

## 7. Licencia y créditos

Proyecto académico, libre para fines educativos. Implementación inspirada
en el clásico capítulo VIII de *Eilenberg, Automata, Languages and Machines*
y el capítulo de monoides sintácticos de Pin (*Mathematical Foundations of
Automata Theory*).
