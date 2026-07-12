# Estudio Algebraico de AFDs vía Monoides de Transición

> 🌐 **Sitio en vivo:** <https://arax48.github.io/syntactic-monoid/web/>
>
> Todo el sitio es **un único archivo HTML** (`web/index.html`) con dos
> secciones: **Autómatas** (regex → AFD mínimo) y **Máquina de Turing**
> (modelo §6.1 desde una descripción de lenguaje). Para cada autómata y
> cada MT generada, la página calcula las propiedades de álgebra
> abstracta que le corresponden: el monoide de transición M(A), sus
> idempotentes, unidades y centro, si es grupo (ℤ/nℤ, V₄, S₃, …),
> abeliano, cíclico o aperiódico (star-free); para lenguajes no
> regulares se explica por qué el monoide sintáctico es infinito.
> Funciona en cualquier navegador moderno, sin instalación.
>
> 📦 La versión anterior del sitio (multi-página: portada, visualizadores
> separados, convenciones y hojas informativas precalculadas) se conserva
> íntegra en la rama
> [`version-anterior-multipagina`](https://github.com/Arax48/syntactic-monoid/tree/version-anterior-multipagina).
> GitHub Pages solo sirve `main`; para ver la versión anterior en el
> navegador, haz checkout de esa rama y abre su `web/index.html` localmente.

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

A partir del 14-06-2026 el código se reorganizó en el paquete `backend/`
(los módulos planos originales se preservan en `legacy/` como referencia
histórica). El paquete está dimensionado para crecer hacia PDAs y Turing
en futuras *slices*.

```
syntactic-monoid/
├── main.py                  # CLI interactiva + subcomandos (importa desde backend/)
├── visualization.py         # Graphviz + matplotlib + reportes
├── web/                     # Sitio estático (sin servidor)
│   └── index.html           # ÚNICO archivo: sección Autómatas + sección MT,
│                            # cada una con su análisis algebraico de M(A)
├── backend/                 # Motor de cómputo
│   ├── models/              # Modelos formales
│   │   ├── dfa.py           # AFD + minimización, producto, equivalencia
│   │   ├── transformation.py# f : Q → Q con propiedades algebraicas
│   │   ├── nfa.py           # AFN / λ-AFN (en construcción)
│   │   ├── pda.py           # PDA (en construcción, slice futura)
│   │   └── turing.py        # Máquina de Turing (en construcción, slice futura)
│   ├── algebra/             # Análisis algebraico
│   │   ├── transition_monoid.py  # M(A) + idempotentes, unidades, centro
│   │   └── homomorphism.py       # φ, núcleo, cociente, primer teorema
│   ├── language/            # Parseo y clasificación de lenguajes (en construcción)
│   └── verification/        # Equivalencia y verificación (en construcción)
├── examples/                # AFDs de ejemplo en JSON
│   ├── parity_afd.json
│   ├── mod3_afd.json
│   └── ends_with_01_afd.json
├── tests/                   # Suite pytest
│   ├── conftest.py
│   ├── test_dfa.py
│   ├── test_transformation.py
│   ├── test_transition_monoid.py
│   └── test_algebra.py
├── legacy/                  # Snapshot de los módulos planos originales
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
1. Cargar AFD
2. Mostrar AFD
3. Evaluar palabra
4. Construir monoide
5. Mostrar transformaciones
6. Mostrar tabla de composición (Cayley)
7. Mostrar núcleo (Ker φ)
8. Mostrar clases de equivalencia
9. Exportar reporte (texto + figuras)
10. Ejecutar ejemplos canónicos
11. Compilar regex a AFD (Thompson + subset construction)
12. Verificar AFD contra regex o muestra accept/reject
13. Generar hoja informativa pedagógica (álgebra + autómatas)
14. Visualizar regex en HTML estático (AFN + AFD + AFD mínimo)
15. **Abrir visualizador interactivo en el navegador** (live, sin terminal)

### Subcomandos directos

```bash
# Resumen + tabla de Cayley
python main.py monoid  examples/parity_afd.json

# Evaluar una palabra
python main.py run     examples/mod3_afd.json 110011

# Generar reporte completo
python main.py report  examples/ends_with_01_afd.json

# Ejecutar los tres ejemplos canónicos
python main.py examples
```

### Subcomandos de la *slice 1* (lenguajes regulares, end-to-end)

```bash
# Compilar una regex a AFD (Thompson + construcción de subconjuntos)
python main.py from-regex "(0|1)*01" --out output/ends_with_01.json

# Verificar que un AFD reconoce el mismo lenguaje que una regex.
# Si difieren, imprime el contraejemplo MÁS CORTO.
python main.py verify examples/mod3_afd.json --regex "0*(10*10*10*)*"

# Verificar contra una muestra accept/reject (también funciona para
# autómatas no decidibles en futuras slices: PDA, TM).
python main.py verify examples/parity_afd.json --samples examples/parity_samples.json

# Hoja informativa pedagógica con la conexión algebraica de M(A):
# ¿es grupo? ¿cuál? ¿qué dice eso del lenguaje?
python main.py infosheet examples/mod3_afd.json --out output/mod3_info.md --markdown

# Visualizar una regex como página HTML autocontenida: muestra el AFN
# de Thompson, el AFD por subconjuntos y el AFD mínimo (Hopcroft) en
# un solo archivo. Auto-abre el navegador.
python main.py visualize "(0|1)*01"
python main.py visualize "[a-c]+.*x" --alphabet abcxy --out output/test.html
python main.py visualize "(0|1)*01" --no-open   # solo genera, no abre
```

### Sitio estático de un solo archivo (sin terminal)

Para acceder al proyecto sin escribir ningún comando, abre
`web/index.html` directamente en tu navegador (doble-clic en el
explorador de archivos), o visita el sitio en vivo. **Todo el sitio es
ese único archivo**, con dos secciones:

**Sección 1 · Autómatas (regex → AFD).** Página autocontenida con el
parser de regex, Thompson (§2.12), subset construction (§2.7.1) y
Hopcroft (§2.16) portados a JavaScript; los grafos se renderizan con
[viz.js](https://github.com/mdaines/viz-js) cargado por CDN.

- Caja de regex con re-render **en vivo** mientras escribes (debounced).
- Caja de alfabeto opcional (con `.` o regexes sin literales hay que dárselo).
- Botones de ejemplos pre-cargados (`(0|1)*01`, paridad, mod 3,
  paridad de a ∧ b ≅ V₄, …).
- Digrafo del AFD mínimo con nota de reducción de estados.
- **Estructura algebraica de M(A)**, calculada en vivo para cada AFD:
  |M(A)| vs la cota |Q|^|Q|, idempotentes, unidades U(M), centro Z(M),
  ¿es grupo?, ¿abeliano?, ¿cíclico (con palabra generadora)?,
  ¿aperiódico? (Schützenberger / star-free) y clasificación
  (ℤ/nℤ, V₄, S₃, …).
- Verificador de palabras con cinta animada paso a paso, sincronizada
  con el resaltado del estado y la transición en el digrafo.

**Sección 2 · Máquina de Turing (§6.1–§6.2).** El modelo completo
(tupla `(Q, q0, F, Σ, Γ, δ)`, cinta bidireccional, blanco `□` externo,
desplazamientos `←/→/−`) portado a JavaScript.

- Entrada por descripción del lenguaje: `a^n b^n c^n`, `#a = #b`,
  `palindromo par`, `ww`, patrones con restricciones (`m >= n`,
  `n >= 1`) y `regex <patrón>` (Teorema 6.1.1: AFD → MT).
- Diagrama de estados con el estado actual resaltado y etiquetas
  de arcos en el formato del libro `s | s' D`.
- Cinta bidireccional animada con cabezal y configuración instantánea
  *u q v* (§6.1); controles paso a paso / animar / pausar.
- **Estructura algebraica**, calculada para cada MT: si el lenguaje es
  regular (`regex …`) se construye M(A) del AFD mínimo equivalente con
  el mismo análisis completo de la sección 1; si el lenguaje no es
  regular (aⁿbⁿ, palíndromos, ww, …) se explica que su monoide
  sintáctico M(L) es infinito y por qué la construcción finita no
  aplica (§3.1).
- Validación estructural según §6.1 (F ≠ ∅, Σ ⊆ Γ, `□ ∉ Γ`,
  no transiciones desde F, δ determinística).

> Requiere internet la primera vez para descargar viz.js (~1 MB).
> Después funciona offline siempre que tu navegador haya cacheado el
> script. Sin internet, se muestra el código DOT plano como fallback.

El visualizador también se puede abrir desde la línea de comandos:

```bash
python main.py interactive
```

### Sintaxis de las expresiones regulares

| Sintaxis | Significado | Ejemplo |
|---|---|---|
| `a` | símbolo literal | `0` reconoce `"0"` |
| `ab` | concatenación | `01` reconoce `"01"` |
| `a\|b` | alternativa | `0\|1` reconoce `"0"` o `"1"` |
| `a*` | cero o más (Kleene) | `0*` reconoce `""`, `"0"`, `"00"`, … |
| `a+` | una o más | `1+` reconoce `"1"`, `"11"`, … |
| `a?` | cero o una | `0?1` reconoce `"1"` o `"01"` |
| `(...)` | agrupación | `(01)*` reconoce `""`, `"01"`, `"0101"`, … |
| `[abc]` | clase de caracteres | `[01]+` = cualquier cadena binaria no vacía |
| `[a-z]` | rango | `[a-c]` = `a`, `b` o `c` |
| `.` | cualquier símbolo del alfabeto | `.*01` = termina en `01` |
| `\x` | literal escapado | `\*` = el carácter `*` |

Precedencia (menor → mayor): unión `|` < concatenación < repetición `* + ?`.

**Nota:** una expresión regular sólo describe lenguajes **regulares**. Lenguajes como `aⁿbⁿ` requieren un PDA o una Máquina de Turing — esto será parte de la *slice 2*.

## 4. Suite de pruebas

```bash
pytest tests/ -v
```

149 pruebas que cubren: validación estructural y operaciones de AFD
(minimización, intersección, equivalencia, contraejemplos); AFN con
λ-transiciones (λ-closure, simulación, subset construction); álgebra
de transformaciones (asociatividad, idempotencia, órbitas, ciclos);
construcción del monoide M(A) (cerradura, cota `|Q|^|Q|`, tabla de
Cayley, idempotentes, unidades, aperiodicidad); propiedades de `φ`
(homomorfismo, reflexividad/simetría/transitividad de `∼`, Primer
Teorema del Isomorfismo); parser de regex y construcción de Thompson;
verificación por equivalencia y por muestras; análisis de estructura
de grupo (ℤ/nℤ, Klein V₄, S₃, …); y generación de la hoja informativa.

## 5. Ejemplos incluidos

| Ejemplo | `\|Q\|` | Lenguaje | `\|M(A)\|` | ¿Grupo? | Estructura |
|--------|---|---|---|---|---|
| `parity_afd.json` | 2 | nº par de 1s | 2 | sí | ≅ ℤ/2ℤ |
| `mod3_afd.json`   | 3 | nº de 1s ≡ 0 (mód 3) | 3 | sí | ≅ ℤ/3ℤ |
| `ends_with_01_afd.json` | 3 | termina en 01 | 5 | no | monoide aperiódico (star-free) |
| `klein_v4_afd.json` | 4 | paridad de `a` ∧ paridad de `b` | 4 | sí | ≅ V₄ = ℤ/2ℤ × ℤ/2ℤ |

Más:

- `parity_samples.json`: muestra accept/reject para `verify --samples`.

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
