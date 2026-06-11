# Estudio Algebraico de Autómatas Finitos Deterministas mediante Monoides de Transición e Implementación Computacional en Python

---

## Portada

**Título del proyecto:** Estudio Algebraico de Autómatas Finitos Deterministas
mediante Monoides de Transición e Implementación Computacional en Python.

**Cursos:** Matemática Discreta II · Teoría de la Computación.

**Periodo académico:** 2026 — Semestre 1.

**Tipo de entregable:** Proyecto integrador final.

---

## 1. Resumen

Este trabajo presenta un estudio integrado, teórico y computacional, de los
Autómatas Finitos Deterministas (DFA) desde una perspectiva algebraica.
Tomando como objeto central el **monoide de transición** `M(A)` asociado a un
DFA `A = (Q, Σ, δ, q₀, F)`, demostramos rigurosamente que la asignación

> `φ : Σ* → M(A),   φ(w) = f_w   con   f_w(q) = δ*(q, w)`

es un homomorfismo sobreyectivo de monoides cuyo núcleo `Ker(φ)` es una
congruencia de monoide sobre `Σ*`. El Primer Teorema del Isomorfismo
proporciona entonces la identificación canónica

> `Σ* / Ker(φ)  ≅  M(A)`,

la cual interpretamos como una **clasificación algebraica de las palabras
según su comportamiento en el autómata**.

Acompañando la fundamentación matemática, desarrollamos una herramienta en
Python (≈900 líneas, 51 pruebas pytest verdes) que: (i) valida y simula DFAs,
(ii) construye `M(A)` por búsqueda en anchura, (iii) genera la tabla de
Cayley, (iv) exhibe el núcleo y los representantes mínimos de cada clase, y
(v) produce reportes en texto plano e imágenes (Graphviz, matplotlib). Se
estudian en detalle tres DFAs canónicos: paridad de unos, conteo módulo 3 y
cadenas que terminan en `01`. En los dos primeros el monoide resulta ser un
grupo abeliano (`ℤ/2ℤ` y `ℤ/3ℤ`); en el tercero, un monoide no conmutativo
de 5 elementos cuya tabla evidencia la asimetría del lenguaje reconocido.

---

## 2. Introducción

La teoría clásica de autómatas suele presentarse como una colección de
construcciones combinatorias (productos cruzados, minimización, equivalencia
con expresiones regulares). El **enfoque algebraico** —iniciado por
Schützenberger y consolidado por Eilenberg, Pin, Reutenauer y Straubing—
ofrece una mirada complementaria: a cada lenguaje regular se le asocian
**monoides finitos** cuya estructura caracteriza propiedades del lenguaje
(p.ej. aperiodicidad, libertad de estrella, complejidad descriptiva).

El presente proyecto se enmarca en este puente entre Matemática Discreta II
(estructuras algebraicas, relaciones de equivalencia, teoremas de
isomorfismo) y Teoría de la Computación (DFAs, lenguajes regulares). El
objeto técnico que estudiamos es el **monoide de transición** `M(A)` —en la
literatura: *transition monoid*— construido directamente a partir de la
función de transición del DFA, sin necesidad de cuocientar el monoide libre
`Σ*` por la congruencia sintáctica del lenguaje. La diferencia con el
**monoide sintáctico** `M(L)` se discute en la sección 4.6.

Objetivos:
1. Formalizar `M(A)` y demostrar sus propiedades de monoide.
2. Definir el homomorfismo natural `φ` y demostrar que efectivamente lo es.
3. Describir `Ker(φ)` como congruencia de `Σ*`, exhibir clases de
   equivalencia y aplicar el Primer Teorema del Isomorfismo.
4. Implementar todo el aparato anterior en Python, con suite de pruebas y
   ejemplos ejecutables.
5. Documentar los resultados en formato académico defendible.

---

## 3. Marco teórico

### 3.1 Alfabetos, palabras y el monoide libre

Un **alfabeto** `Σ` es un conjunto finito no vacío cuyos elementos llamamos
**símbolos** o **letras**. Una **palabra** sobre `Σ` es una secuencia finita
`w = a₁a₂…a_n` con cada `aᵢ ∈ Σ`. La longitud de `w` es `|w| = n`. La palabra
de longitud cero es la **palabra vacía** `ε`.

Denotamos por `Σ*` al conjunto de todas las palabras sobre `Σ`, incluyendo
`ε`. La **concatenación** `· : Σ* × Σ* → Σ*` es asociativa y `ε` es su
elemento neutro. Por tanto `(Σ*, ·, ε)` es un monoide: el **monoide libre**
generado por `Σ`. Es libre porque toda función `Σ → M` hacia un monoide `M`
se extiende de manera única a un homomorfismo de monoides `Σ* → M`.

Un **lenguaje** sobre `Σ` es cualquier subconjunto `L ⊆ Σ*`.

### 3.2 Autómatas Finitos Deterministas

Un **DFA** es una 5-tupla `A = (Q, Σ, δ, q₀, F)` con:
- `Q`: conjunto finito de estados.
- `Σ`: alfabeto.
- `δ : Q × Σ → Q`: función de transición (total).
- `q₀ ∈ Q`: estado inicial.
- `F ⊆ Q`: conjunto de estados de aceptación.

La función de transición se extiende a palabras como `δ* : Q × Σ* → Q`
mediante:

> `δ*(q, ε) = q`,
> `δ*(q, wa) = δ(δ*(q, w), a)`  para todo `w ∈ Σ*` y `a ∈ Σ`.

El **lenguaje aceptado** por `A` es
`L(A) = { w ∈ Σ* : δ*(q₀, w) ∈ F }`. Un lenguaje es **regular** si y sólo
si es aceptado por algún DFA.

### 3.3 Monoides y homomorfismos

Un **monoide** es una tripla `(M, ⋆, e)` con `⋆` operación binaria asociativa
sobre `M` y `e ∈ M` elemento neutro a ambos lados. Un **homomorfismo de
monoides** entre `(M, ⋆, e)` y `(N, ⊗, e')` es una función `h : M → N` que
preserva la operación y el neutro: `h(x ⋆ y) = h(x) ⊗ h(y)` y `h(e) = e'`.

Una **congruencia de monoide** sobre `M` es una relación de equivalencia
`~` compatible con la operación: si `x ∼ x'` y `y ∼ y'` entonces
`x ⋆ y ∼ x' ⋆ y'`. El conjunto cociente `M/∼` hereda entonces una estructura
de monoide, y la proyección canónica `π : M → M/∼` es un homomorfismo.

**Primer Teorema del Isomorfismo (monoides).** Si `h : M → N` es un
homomorfismo de monoides, la relación `x ∼_h y ⟺ h(x) = h(y)` es una
congruencia y existe un único isomorfismo `h̄ : M / ∼_h → Im(h)` tal que
`h = h̄ ∘ π`. La demostración es análoga a la versión para grupos: se
define `h̄([x]) = h(x)`, se verifica buena definición, homomorfismo,
inyectividad y sobreyectividad sobre `Im(h)`.

---

## 4. Fundamentación matemática

A lo largo de esta sección fijamos un DFA `A = (Q, Σ, δ, q₀, F)`.

### 4.1 Transformaciones inducidas por palabras

Para cada `w ∈ Σ*` definimos la transformación

> `f_w : Q → Q,   f_w(q) = δ*(q, w)`.

**Caso base.** `f_ε(q) = δ*(q, ε) = q`, luego `f_ε = id_Q`.

**Composición.** Para `u, v ∈ Σ*` y `q ∈ Q`,

> `f_{uv}(q) = δ*(q, uv) = δ*(δ*(q, u), v) = f_v(f_u(q)) = (f_v ∘ f_u)(q)`.

Es decir,

> `f_{uv} = f_v ∘ f_u`.   *(★)*

Observación de orden: como leemos la palabra de izquierda a derecha,
**primero se aplica `f_u` y después `f_v`**. En la implementación esto se
codifica con el método `Transformation.then(other)`: `f_u.then(f_v) = f_{uv}`.

### 4.2 Definición y existencia de `M(A)`

Sea
> `M(A) = { f_w : w ∈ Σ* } ⊆ Q^Q`.

**Lema 1 (Cerradura).** `M(A)` es cerrado bajo la composición de funciones.

*Demostración.* Por (★), si `f_u, f_v ∈ M(A)` entonces
`f_v ∘ f_u = f_{uv} ∈ M(A)`. ∎

**Lema 2 (Asociatividad).** La composición de funciones es asociativa en
`Q^Q`, en particular en `M(A)`.

*Demostración.* Para todo `q ∈ Q`,
`((f ∘ g) ∘ h)(q) = (f ∘ g)(h(q)) = f(g(h(q))) = f((g ∘ h)(q)) = (f ∘ (g ∘ h))(q)`. ∎

**Lema 3 (Identidad).** `id_Q = f_ε ∈ M(A)` y es neutra a ambos lados.

*Demostración.* `f_ε ∈ M(A)` por definición. Para cualquier `f_w`,
`f_w ∘ f_ε = f_{εw} = f_w = f_{wε} = f_ε ∘ f_w` por (★) y las
propiedades de la concatenación. ∎

**Teorema 1.** `(M(A), ∘, id_Q)` es un monoide finito y `|M(A)| ≤ |Q|^|Q|`.

*Demostración.* Cerradura, asociatividad y existencia de neutro están
probadas. La cota se sigue de que `M(A) ⊆ Q^Q` y `|Q^Q| = |Q|^|Q|`. ∎

### 4.3 El homomorfismo natural `φ`

Definimos `φ : Σ* → M(A)` por `φ(w) = f_w`.

**Teorema 2 (φ es homomorfismo).** Para todo `u, v ∈ Σ*`:

> `φ(uv) = φ(u) ⋆ φ(v)`

donde `⋆` denota la operación de `M(A)` cuando vemos `f_u` aplicada antes que
`f_v`. Concretamente, definiendo `f ⋆ g := g ∘ f` (i.e. "primero `f`, luego
`g`"), tenemos `φ(uv) = φ(u) ⋆ φ(v)` y `φ(ε) = id_Q`.

*Demostración.* Por (★),
`φ(uv) = f_{uv} = f_v ∘ f_u = φ(u) ⋆ φ(v)` y `φ(ε) = f_ε = id_Q`. ∎

**Observación de implementación.** En el código, `⋆` corresponde al método
`Transformation.then`: dado `f = φ(u)` y `g = φ(v)`,
`f.then(g) = φ(uv)`. Esto evita confusiones con el orden estándar de la
composición funcional (`(g ∘ f)(q) = g(f(q))`), y nos permite trabajar con
notación de lectura izquierda-a-derecha de palabras, que es la convención
natural en autómatas.

**Teorema 3 (φ es sobreyectivo).** `Im(φ) = M(A)`.

*Demostración.* Por construcción `M(A) = { f_w : w ∈ Σ* } = Im(φ)`. ∎

### 4.4 Núcleo de `φ` y la congruencia `∼`

Definimos sobre `Σ*` la relación

> `u ∼ v  ⟺  φ(u) = φ(v)  ⟺  f_u = f_v`.

**Proposición 1.** `∼` es una relación de equivalencia.

*Demostración.* Reflexividad: `f_u = f_u`. Simetría: `f_u = f_v ⇒ f_v = f_u`.
Transitividad: `f_u = f_v ∧ f_v = f_w ⇒ f_u = f_w`. ∎

**Proposición 2 (`∼` es congruencia de monoide).** Si `u ∼ u'` y `v ∼ v'`,
entonces `uv ∼ u'v'`.

*Demostración.* Por (★),
`f_{uv} = f_v ∘ f_u = f_{v'} ∘ f_{u'} = f_{u'v'}`. ∎

Definimos `Ker(φ) := ∼`. En la literatura de monoides al núcleo de un
homomorfismo se le llama también **congruencia inducida** por `φ`.

**Interpretación operativa.** Dos palabras `u, v` son `∼`-equivalentes si y
sólo si **no se distinguen por el autómata desde ningún estado**: para todo
`q ∈ Q`, `δ*(q, u) = δ*(q, v)`. Es una condición considerablemente más fuerte
que `δ*(q₀, u) = δ*(q₀, v)`.

### 4.5 Clases de equivalencia y cociente

Por la Proposición 1, las clases `[u]_∼ = { v ∈ Σ* : v ∼ u }` particionan
`Σ*`. El conjunto cociente `Σ* / Ker(φ)` hereda la estructura de monoide,
con operación

> `[u] ⋆ [v] := [uv]`,

bien definida por la Proposición 2. La identidad es `[ε]`.

**Teorema 4 (Primer Teorema del Isomorfismo).** Existe un único isomorfismo
de monoides

> `φ̄ : Σ* / Ker(φ)  →  M(A)`

tal que `φ = φ̄ ∘ π`, donde `π : Σ* → Σ*/Ker(φ)` es la proyección canónica.

*Demostración.* Definimos `φ̄([w]) := φ(w) = f_w`.
- **Buena definición.** Si `[w] = [w']`, entonces `w ∼ w'`, es decir
  `φ(w) = φ(w')`, de modo que el valor asignado no depende del representante.
- **Homomorfismo.** `φ̄([u][v]) = φ̄([uv]) = φ(uv) = φ(u) ⋆ φ(v) = φ̄([u]) ⋆ φ̄([v])`
  por el Teorema 2. Además `φ̄([ε]) = φ(ε) = id_Q`.
- **Inyectividad.** Si `φ̄([u]) = φ̄([v])`, entonces `φ(u) = φ(v)`, luego
  `u ∼ v` y `[u] = [v]`.
- **Sobreyectividad sobre `Im(φ)`.** Para todo `f ∈ Im(φ)` existe `w ∈ Σ*`
  con `φ(w) = f`, y entonces `φ̄([w]) = f`.
- **Unicidad.** Cualquier `ψ` que cumpla `φ = ψ ∘ π` debe satisfacer
  `ψ([w]) = ψ(π(w)) = φ(w) = φ̄([w])`. ∎

Combinando con el Teorema 3:

> **Corolario 1.** `Σ* / Ker(φ)  ≅  M(A)`.

### 4.6 Nota: monoide de transición vs. monoide sintáctico

El **monoide sintáctico** `M(L)` de un lenguaje `L ⊆ Σ*` se define mediante
la congruencia sintáctica `∼_L`:

> `u ∼_L v  ⟺  ∀ x, y ∈ Σ*: xuy ∈ L ⇔ xvy ∈ L`.

`M(L) := Σ* / ∼_L`. Si `A` es el **DFA mínimo** que reconoce `L`, entonces
`M(A) ≅ M(L)`. Si `A` no es mínimo, en general `M(A)` es un monoide más
grande que admite a `M(L)` como cociente. En este proyecto tomamos `M(A)`
como objeto principal porque (i) se construye algorítmicamente sin
minimización previa y (ii) ya es suficiente para ilustrar el aparato
algebraico completo.

---

## 5. Metodología

El proyecto sigue una metodología **constructiva y verificable**:
1. **Modelado matemático.** Cada definición y teorema de §4 se expone con
   demostración detallada.
2. **Diseño orientado a objetos.** Cada concepto matemático se materializa en
   una clase Python con responsabilidades únicas (`DFA`, `Transformation`,
   `TransitionMonoid`, `Homomorphism`).
3. **Algoritmo BFS** para construir `M(A)`: se inicia con la identidad y se
   aplica cada generador del alfabeto, deteniéndose cuando no aparecen
   transformaciones nuevas. Termina en a lo sumo `|M(A)| ≤ |Q|^|Q|` pasos.
4. **Verificación empírica.** Para cada DFA de ejemplo se prueba
   computacionalmente que `φ(uv) = φ(u) ⋆ φ(v)`, que `∼` es de equivalencia
   y que `|Σ*/Ker(φ)| = |M(A)|`.
5. **Pruebas unitarias** (`pytest`) en todos los módulos.
6. **Visualización** del DFA (Graphviz), tabla de Cayley (matplotlib) y
   reporte textual.

---

## 6. Desarrollo algebraico (ejemplos)

### 6.1 Ejemplo 1: paridad de unos

`Σ = {0, 1}`, `Q = {Par, Impar}`, `q₀ = Par`, `F = {Par}`,
`δ(Par,0)=Par`, `δ(Par,1)=Impar`, `δ(Impar,0)=Impar`, `δ(Impar,1)=Par`.

**Transformaciones generadoras.**
- `f_0`: identidad (`Par→Par`, `Impar→Impar`).
- `f_1`: intercambio (`Par→Impar`, `Impar→Par`).

**Monoide.** `M(A) = { id, swap }` con `swap ∘ swap = id`. Es isomorfo a
`(ℤ/2ℤ, +, 0)`.

**Tabla de Cayley** (con `e = id, 1 = swap`):

|     | e | 1 |
|-----|---|---|
| **e** | e | 1 |
| **1** | 1 | e |

**Núcleo.** `u ∼ v ⟺ |u|_1 ≡ |v|_1 (mód 2)`. Dos clases: palabras con
número par de unos (incluye `ε`, `00`, `11`, `0110`, …) y palabras con
número impar de unos (`1`, `10`, `01`, `111`, …).

**Primer Teorema:** `Σ*/Ker(φ) = {[ε], [1]} ≅ ℤ/2ℤ ≅ M(A)`.

### 6.2 Ejemplo 2: cantidad de 1s ≡ 0 (mód 3)

`Σ = {0, 1}`, `Q = {r0, r1, r2}`, `q₀ = r0`, `F = {r0}`.
La cifra `0` no cambia el estado; la cifra `1` lo incrementa módulo 3.

**Generadores.**
- `f_0 = id_Q`.
- `f_1 = (r0→r1, r1→r2, r2→r0)`, el ciclo de longitud 3.

**Monoide.** `M(A) = { id, f_1, f_1² }` con `f_1³ = id`. Es isomorfo a
`(ℤ/3ℤ, +, 0)`.

**Tabla de Cayley** (con `e = id, 1 = f_1, 11 = f_1²`):

|     | e | 1 | 11 |
|-----|---|---|----|
| **e**  | e  | 1  | 11 |
| **1**  | 1  | 11 | e  |
| **11** | 11 | e  | 1  |

**Núcleo.** `u ∼ v ⟺ |u|_1 ≡ |v|_1 (mód 3)`. Tres clases.

### 6.3 Ejemplo 3: cadenas que terminan en `01`

`Σ = {0, 1}`, `Q = {s0, s1, s2}`, `q₀ = s0`, `F = {s2}`.
`δ(s0,0)=s1`, `δ(s0,1)=s0`, `δ(s1,0)=s1`, `δ(s1,1)=s2`, `δ(s2,0)=s1`,
`δ(s2,1)=s0`. `s2` representa "acabo de leer `01`".

**Generadores.**
- `f_0 = (s0→s1, s1→s1, s2→s1)`: tras leer `0`, sólo se puede estar en `s1`.
- `f_1 = (s0→s0, s1→s2, s2→s0)`.

**Monoide.** Tras la BFS aparecen exactamente 5 transformaciones distintas,
con representantes mínimos `ε, 0, 1, 01, 11`. El monoide **no** es un grupo
(la mayoría de transformaciones tienen imagen contenida estrictamente en
`Q` y no son invertibles), tampoco es conmutativo. Su tabla de Cayley
calculada por el programa es:

```
    |  e   0   1   01  11
----+--------------------
e   |  e   0   1   01  11
0   |  0   0   01  01  11
1   |  1   0   11  01  11
01  |  01  0   11  01  11
11  |  11  0   11  01  11
```

**Núcleo (hasta `|w| ≤ 3`).**

| Clase | Palabras representativas |
|-------|--------------------------|
| `[ε]`  | `ε` |
| `[0]`  | `0, 00, 10, 000, 010, 100, 110` |
| `[1]`  | `1` |
| `[01]` | `01, 001, 101` |
| `[11]` | `11, 011, 111` |

`Σ*/Ker(φ)` tiene 5 elementos, en bijección con `M(A)`. La asimetría de la
tabla confirma que el monoide es **aperiódico**: la palabra `00 ∼ 0` y
`11 ≠ 1`, etc.

---

## 7. Implementación computacional

### 7.1 Vista general

| Módulo | Responsabilidad | LOC aprox. |
|--------|-----------------|------------|
| `dfa.py` | Clase `DFA`, validación, `δ*`, ejecución, tabla. | 200 |
| `transformation.py` | Clase `Transformation`, composición, hash. | 130 |
| `transition_monoid.py` | Clase `TransitionMonoid`, BFS, Cayley, propiedades. | 220 |
| `algebra.py` | Clase `Homomorphism`, `φ`, núcleo, cociente, isomorfismo. | 150 |
| `visualization.py` | Graphviz, matplotlib, reportes. | 200 |
| `main.py` | CLI interactivo + argparse. | 250 |

### 7.2 Decisiones de diseño relevantes

- **`Transformation` es inmutable y hasheable**, lo que permite usarla como
  clave en `dict`/`set` durante la BFS sin pagar el costo de comparar
  diccionarios elemento a elemento. Internamente almacena una tupla ordenada
  de pares `(q, f(q))`.
- **Orden de composición.** Distinguimos `then` (orden de lectura,
  `f.then(g) = f_{uv}` cuando `f = f_u, g = f_v`) y `compose` (orden
  matemático clásico, `f.compose(g) = f ∘ g`). Esto evita el error clásico
  de invertir el orden de la concatenación.
- **BFS con representantes mínimos.** La cola se procesa en orden FIFO y los
  símbolos del alfabeto siempre se aplican en orden lexicográfico, lo que
  garantiza que la palabra representante de cada transformación sea la más
  corta y, entre las de igual longitud, la lexicográficamente menor.
- **`Homomorphism.kernel`** devuelve una aproximación finita del núcleo
  (palabras con `|w| ≤ N`). Para `N ≥ |M(A)|`, toda transformación se ha
  alcanzado, por lo que la verificación del Primer Teorema es exacta.
- **Visualización opcional.** Las funciones de `visualization.py` importan
  `graphviz`/`matplotlib` localmente para que el resto del proyecto sea
  utilizable en entornos sin librerías gráficas.

### 7.3 Algoritmo de construcción de `M(A)`

```
Entrada: DFA A = (Q, Σ, δ, q0, F)
Salida : conjunto M(A) ⊆ Q^Q y, para cada f ∈ M(A), una palabra rep(f).

1. Para cada a ∈ Σ, calcular el generador g_a(q) = δ(q, a).
2. Crear M ← {id_Q}, queue ← [(ε, id_Q)], rep(id_Q) ← ε.
3. Mientras queue no esté vacía:
   a. Desencolar (w, f).
   b. Para cada a ∈ Σ (en orden):
        h ← f.then(g_a)              # h = f_{wa}
        si h ∉ M:
            M.add(h); rep(h) ← w·a
            queue.append((w·a, h))
4. Devolver (M, rep).
```

Como la cola sólo crece cuando aparece una transformación nueva y
`|M(A)| ≤ |Q|^|Q|`, el algoritmo termina. El tiempo total es
`O(|Σ| · |M(A)| · |Q|)`.

---

## 8. Resultados experimentales

Se ejecutó el programa sobre los tres DFAs incluidos. La siguiente tabla
resume las métricas observadas (todas verificadas por `pytest`):

| DFA | `\|Q\|` | `\|M(A)\|` | Cota `\|Q\|^\|Q\|` | Conmutativo | Grupo | Estructura conocida |
|----|--------|--------|----------|-----|------|---------------|
| Paridad | 2 | 2 | 4 | sí | sí | `ℤ/2ℤ` |
| Mód 3   | 3 | 3 | 27 | sí | sí | `ℤ/3ℤ` |
| Termina en `01` | 3 | 5 | 27 | no | no | monoide aperiódico |

Para cada DFA, la suite verifica además:
- `φ(uv) = φ(u).then(φ(v))` para toda `(u, v)` con `|u|, |v| ≤ 4`.
- `∼` es una relación de equivalencia (reflexividad, simetría,
  transitividad).
- `|Σ*/Ker(φ)| = |M(A)|`, lo que valida empíricamente el Primer Teorema
  del Isomorfismo (Corolario 1).

Salida típica del programa (`python main.py monoid examples/mod3_dfa.json`):

```
Monoide de transicion M(A) de Numero de 1s congruente con 0 mod 3
  |Q|        = 3
  |Sigma|    = 2
  |M(A)|     = 3
  Cota |Q|^|Q| = 27
  Conmutativo = True
  Grupo       = True

    |  e   1   11
----+------------
e   |  e   1   11
1   |  1   11  e
11  |  11  e   1
```

---

## 9. Discusión

1. **Naturaleza del monoide.** En los DFAs construidos sobre operaciones
   "modulares" (paridad, mód 3) los monoides resultan ser grupos cíclicos.
   Esto refleja un hecho general: si todos los símbolos inducen biyecciones
   sobre `Q`, entonces `M(A)` es un grupo (es un subgrupo del grupo
   simétrico `S_Q`).
2. **DFAs con "estados absorbentes lectorialmente".** En el ejemplo `01`,
   los símbolos colapsan el dominio (la lectura de un `0` deja siempre el
   estado en `s1`), por lo que las transformaciones no son inyectivas y el
   monoide no puede ser un grupo. Esto es consistente con la teoría: el
   lenguaje "termina en `01`" es libre de estrella, y el monoide sintáctico
   de un lenguaje libre de estrella es aperiódico (Teorema de
   Schützenberger).
3. **Cota `|Q|^|Q|`.** El ejemplo `01` muestra que la cota dista mucho de
   ser estrecha (5 vs. 27). En general, identificar `|M(A)|` exactamente es
   un problema *no trivial*: existen lenguajes regulares cuyos monoides
   sintácticos crecen exponencialmente en `|Q|`.
4. **Limitación del cociente truncado.** Computacionalmente no podemos
   exhibir clases infinitas de `Σ*`, pero exhibirlas hasta `|w| ≤ N` con
   `N ≥ |M(A)|` es suficiente para verificar el isomorfismo, porque la BFS
   garantiza que toda transformación aparece en a lo sumo `|M(A)|` pasos.

---

## 10. Conclusiones

- Se logró un **desarrollo riguroso** del marco algebraico que vincula DFAs
  y monoides, con demostraciones completas de cerradura, asociatividad,
  identidad, homomorfismo y Primer Teorema del Isomorfismo.
- Se construyó una herramienta Python **ejecutable, modular y probada**
  (51/51 tests verdes) que materializa fielmente las definiciones
  matemáticas y permite explorar interactivamente cualquier DFA dado en
  JSON.
- Los tres ejemplos canónicos ilustran tanto el caso "grupo" (paridad,
  módulo 3) como el caso "monoide aperiódico" (`01`), mostrando que la
  estructura algebraica capta información cualitativa del lenguaje.
- La integración entre **Matemática Discreta II** (estructuras algebraicas,
  relaciones, teoremas de isomorfismo) y **Teoría de la Computación** (DFAs,
  lenguajes regulares) queda explícita y operativa.

---

## 11. Trabajo futuro

- Implementar el **monoide sintáctico** `M(L)` mediante minimización del DFA
  y verificar `M(A_min) ≅ M(L)`.
- Detectar **aperiodicidad** del monoide y, en consecuencia, **libertad de
  estrella** del lenguaje (Schützenberger).
- Extender a **autómatas con salida** (transductores) y al **monoide
  sintáctico de relaciones racionales**.
- Conectar con la jerarquía de **variedades de monoides** (Eilenberg) y
  caracterizaciones algebraicas de subclases de lenguajes regulares.
- Generar reportes en **LaTeX/PDF** automáticamente desde `visualization.py`.
- Implementar **representación matricial** de transformaciones para escalar
  a DFAs con cientos de estados.

---

## 12. Referencias

1. Eilenberg, S. *Automata, Languages and Machines, Vol. A & B.* Academic
   Press, 1974–1976.
2. Pin, J.-É. *Mathematical Foundations of Automata Theory.* Disponible en
   línea, versión actualizada 2020.
3. Sipser, M. *Introduction to the Theory of Computation,* 3.ª ed., Cengage,
   2012.
4. Hopcroft, J. E.; Motwani, R.; Ullman, J. D. *Introduction to Automata
   Theory, Languages, and Computation,* 3.ª ed., Addison-Wesley, 2007.
5. Howie, J. M. *Fundamentals of Semigroup Theory.* Oxford University Press,
   1995.
6. Lallement, G. *Semigroups and Combinatorial Applications.* Wiley, 1979.
7. Rotman, J. J. *An Introduction to the Theory of Groups,* 4.ª ed.,
   Springer, 1995. (Para el Primer Teorema del Isomorfismo en su versión
   clásica.)
8. Straubing, H. *Finite Automata, Formal Logic, and Circuit Complexity.*
   Birkhäuser, 1994.
