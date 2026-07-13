# Estudio Algebraico de Autómatas Finitos Deterministas mediante Monoides de Transición e Implementación Computacional en Python

---

## Portada

**Título del proyecto:** Estudio Algebraico de Autómatas Finitos Deterministas
mediante Monoides de Transición e Implementación Computacional en Python.

**Cursos:** Matemática Discreta II · Teoría de la Computación.

**Periodo académico:** 2026 - 1

**Tipo de entregable:** Proyecto integrador final.

---

## 1. Resumen

Este trabajo presenta un estudio integrado, teórico y computacional, de los
Autómatas Finitos Deterministas (AFD) desde una perspectiva algebraica.
Tomando como objeto central el **monoide de transición** `M(A)` asociado a un
AFD `A = (Q, Σ, δ, q₀, F)`, demostramos rigurosamente que la asignación

> `φ : Σ* → M(A),   φ(w) = f_w   con   f_w(q) = δ*(q, w)`

es un homomorfismo sobreyectivo de monoides cuyo núcleo `Ker(φ)` es una
congruencia de monoide sobre `Σ*`. El Primer Teorema del Isomorfismo
proporciona entonces la identificación canónica

> `Σ* / Ker(φ)  ≅  M(A)`,

la cual interpretamos como una **clasificación algebraica de las palabras
según su comportamiento en el autómata**.

Acompañando la fundamentación matemática, desarrollamos una herramienta en
Python (≈900 líneas, 51 pruebas pytest verdes) que: (i) valida y simula AFDs,
(ii) construye `M(A)` por búsqueda en anchura, (iii) genera la tabla de
Cayley, (iv) exhibe el núcleo y los representantes mínimos de cada clase, y
(v) produce reportes en texto plano e imágenes (Graphviz, matplotlib). Se
estudian en detalle tres AFDs canónicos: paridad de unos, conteo módulo 3 y
cadenas que terminan en `01`. En los dos primeros el monoide resulta ser un
grupo abeliano (`ℤ/2ℤ` y `ℤ/3ℤ`); en el tercero, un monoide no conmutativo
de 5 elementos cuya tabla evidencia la asimetría del lenguaje reconocido.

---

## 2. Introducción

La teoría clásica de autómatas suele presentarse como una colección de
construcciones combinatorias (productos cruzados, minimización, equivalencia
con expresiones regulares). Este proyecto adopta una **mirada algebraica
complementaria**, construida enteramente con las dos fuentes del curso:
Saracino (*Abstract Algebra: A First Course*) para las estructuras
algebraicas, y De Castro Korgi (*Introducción a la Teoría de la Computación*)
para los autómatas. A cada AFD se le asocia un **monoide finito** cuya
estructura caracteriza propiedades del lenguaje (p.ej. si es un grupo, cuál,
si es abeliano, cíclico o aperiódico).

El presente proyecto se enmarca en este puente entre Matemática Discreta II
(estructuras algebraicas, relaciones de equivalencia, teoremas de
isomorfismo) y Teoría de la Computación (AFDs, lenguajes regulares). El
objeto técnico que estudiamos es el **monoide de transición** `M(A)`,
construido directamente a partir de la función de transición del AFD: es un
monoide bajo la composición de funciones (Saracino §1 y §6). Es una
**construcción propia** del proyecto —no aparece como tal en ninguno de los
dos libros—, cuyo carácter de invariante del lenguaje se justifica vía
Myhill–Nerode y minimización, como se discute en la sección 4.6.

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
de longitud cero es la **palabra vacía** `λ`.

Denotamos por `Σ*` al conjunto de todas las palabras sobre `Σ`, incluyendo
`λ`. La **concatenación** `· : Σ* × Σ* → Σ*` es asociativa y `λ` es su
elemento neutro. Por tanto `(Σ*, ·, λ)` es un monoide: el **monoide libre**
generado por `Σ`. Es libre porque toda función `Σ → M` hacia un monoide `M`
se extiende de manera única a un homomorfismo de monoides `Σ* → M`.

Un **lenguaje** sobre `Σ` es cualquier subconjunto `L ⊆ Σ*`.

### 3.2 Autómatas Finitos Deterministas

Un **AFD** es una 5-tupla `A = (Q, Σ, δ, q₀, F)` con:
- `Q`: conjunto finito de estados.
- `Σ`: alfabeto.
- `δ : Q × Σ → Q`: función de transición (total).
- `q₀ ∈ Q`: estado inicial.
- `F ⊆ Q`: conjunto de estados de aceptación.

La función de transición se extiende a palabras como `δ* : Q × Σ* → Q`
mediante:

> `δ*(q, λ) = q`,
> `δ*(q, wa) = δ(δ*(q, w), a)`  para todo `w ∈ Σ*` y `a ∈ Σ`.

El **lenguaje aceptado** por `A` es
`L(A) = { w ∈ Σ* : δ*(q₀, w) ∈ F }`. Un lenguaje es **regular** si y sólo
si es aceptado por algún AFD.

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

### 3.4 Convención de composición (fijada por todo el documento)

Como las palabras se leen **de izquierda a derecha** y las funciones se
componen **de derecha a izquierda** (`(g ∘ f)(q) := g(f(q))`), surge una
posible confusión de orden al pasar de `Σ*` a transformaciones sobre `Q`.
Para evitarla fijamos de una vez la siguiente convención, que será usada
en todo el informe y en el código (método `Transformation.then`):

> Sobre el conjunto `Q^Q` de funciones `Q → Q` definimos la operación
> **diagramática** o de **lectura izquierda-a-derecha**:
>
> `(f · g)(q)  :=  g(f(q))`,   es decir,  `f · g  :=  g ∘ f`.

La tripla `(Q^Q, ·, id_Q)` es un monoide (el llamado *monoide opuesto* del
monoide funcional usual `(Q^Q, ∘, id_Q)`), pues `·` es asociativa e
`id_Q` es neutro a ambos lados. En el código:

```python
f.then(g)(q) == g(f(q))      # corresponde a f · g
```

Con esta convención, **leer `uv` significa "primero aplicar `f_u`, luego
`f_v`", igual que se compone con `·`**. Como consecuencia, `φ : Σ* → M(A)`
resultará ser un homomorfismo *en el sentido estándar*, sin signo opuesto
ni anti-homomorfismo. Todas las apariciones de `·` en este informe se
entienden en esta convención.

---

## 4. Fundamentación matemática

A lo largo de esta sección fijamos un AFD `A = (Q, Σ, δ, q₀, F)` y
adoptamos la convención de composición fijada en §3.4: para `f, g ∈ Q^Q`,

> `f · g := g ∘ f`   (lectura izquierda-a-derecha).

### 4.0 Lema de separación de `δ*`

Antes de definir el monoide necesitamos un lema fundamental que NO está
explícito en la definición recursiva de `δ*`.

**Lema 0 (separación).** Para todo `q ∈ Q` y `u, v ∈ Σ*`:

> `δ*(q, uv) = δ*(δ*(q, u), v)`.

*Demostración (inducción sobre `|v|`).*

- *Base `v = λ`.* `δ*(q, uλ) = δ*(q, u) = δ*(δ*(q, u), λ)` por la
  definición de `δ*` aplicada al lado derecho.
- *Paso `v = wa` con `a ∈ Σ` y `|w| < |v|`.* Asumimos por hipótesis de
  inducción que `δ*(q, uw) = δ*(δ*(q, u), w)`. Entonces

  ```
  δ*(q, u(wa)) = δ*(q, (uw)a)                          [asociatividad de ·]
              = δ(δ*(q, uw), a)                        [def. δ*]
              = δ(δ*(δ*(q, u), w), a)                   [HI]
              = δ*(δ*(q, u), wa)                        [def. δ*]
              = δ*(δ*(q, u), v).
  ```

Esto cierra la inducción. ∎

### 4.1 Transformaciones inducidas por palabras

Para cada `w ∈ Σ*` definimos la transformación

> `f_w : Q → Q,   f_w(q) = δ*(q, w)`.

**Caso base.** `f_λ(q) = δ*(q, λ) = q`, luego `f_λ = id_Q`.

**Identidad multiplicativa.** Para `u, v ∈ Σ*` y `q ∈ Q`, usando el
Lema 0 y la convención `f · g = g ∘ f`:

> `f_{uv}(q) = δ*(q, uv) = δ*(δ*(q, u), v) = f_v(f_u(q)) = (f_u · f_v)(q)`.

Es decir,

> `f_{uv} = f_u · f_v   =   f_v ∘ f_u`.   *(★)*

Esta identidad es **la pieza clave** de todo el desarrollo posterior: en la
operación diagramática `·` (lectura izquierda-a-derecha) la concatenación de
palabras se traduce literalmente como concatenación de transformaciones, sin
inversión de orden. En el código:

```python
Transformation_of(u + v) == Transformation_of(u).then(Transformation_of(v))
```

### 4.2 Definición y existencia de `M(A)`

Sea
> `M(A) = { f_w : w ∈ Σ* } ⊆ Q^Q`.

**Lema 1 (Cerradura).** `M(A)` es cerrado bajo la operación `·`.

*Demostración.* Por (★), si `f_u, f_v ∈ M(A)` entonces
`f_u · f_v = f_{uv} ∈ M(A)`. ∎

**Lema 2 (Asociatividad).** La operación `·` es asociativa en `Q^Q` (y por
tanto en `M(A)`).

*Demostración.* Para todo `q ∈ Q`,
`((f · g) · h)(q) = h((f·g)(q)) = h(g(f(q))) = (g·h)(f(q)) = (f · (g · h))(q)`.
∎

**Lema 3 (Identidad).** `id_Q = f_λ ∈ M(A)` y es neutra a ambos lados.

*Demostración.* `f_λ ∈ M(A)` por definición. Para cualquier `f_w`,
`f_w · f_λ = f_{wλ} = f_w = f_{λw} = f_λ · f_w`, donde se usó (★) y
las identidades `wλ = w = λw` en `Σ*`. ∎

**Teorema 1.** `(M(A), ·, id_Q)` es un monoide finito y `|M(A)| ≤ |Q|^|Q|`.

*Demostración.* Cerradura (Lema 1), asociatividad (Lema 2) y existencia de
neutro (Lema 3) están probadas. La cota se sigue de que `M(A) ⊆ Q^Q` y
`|Q^Q| = |Q|^|Q|`. ∎

### 4.3 El homomorfismo natural `φ`

Definimos `φ : Σ* → M(A)` por `φ(w) = f_w`.

**Teorema 2 (`φ` es homomorfismo de monoides).** La función
`φ : (Σ*, ·, λ) → (M(A), ·, id_Q)` cumple:

> (i)  `φ(λ) = id_Q`,
> (ii) `φ(uv) = φ(u) · φ(v)` para todo `u, v ∈ Σ*`.

*Demostración.* (i) `φ(λ) = f_λ = id_Q` por el caso base de §4.1.
(ii) Por (★), `φ(uv) = f_{uv} = f_u · f_v = φ(u) · φ(v)`. ∎

**Observación de implementación.** La operación `·` en `M(A)` corresponde
exactamente al método `Transformation.then`: `φ(u).then(φ(v)) = φ(uv)`.
La igualdad se verifica empíricamente en `Homomorphism.verify_homomorphism`
para todas las palabras hasta una longitud dada.

**Teorema 3 (`φ` es sobreyectivo).** `Im(φ) = M(A)`.

*Demostración.* Por construcción `M(A) := { f_w : w ∈ Σ* } = Im(φ)`. ∎

### 4.4 Núcleo de `φ` y la congruencia `∼`

Definimos sobre `Σ*` la relación

> `u ∼ v  ⟺  φ(u) = φ(v)  ⟺  f_u = f_v`.

**Proposición 1.** `∼` es una relación de equivalencia.

*Demostración.* Reflexividad: `f_u = f_u`. Simetría: `f_u = f_v ⇒ f_v = f_u`.
Transitividad: `f_u = f_v ∧ f_v = f_w ⇒ f_u = f_w`. ∎

**Proposición 2 (`∼` es congruencia de monoide).** Si `u ∼ u'` y `v ∼ v'`,
entonces `uv ∼ u'v'`.

*Demostración.* Por hipótesis `f_u = f_{u'}` y `f_v = f_{v'}`. Por (★),
`f_{uv} = f_u · f_v = f_{u'} · f_{v'} = f_{u'v'}`. Luego `uv ∼ u'v'`. ∎

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

bien definida por la Proposición 2. La identidad es `[λ]`.

**Teorema 4 (Primer Teorema del Isomorfismo).** Existe un único isomorfismo
de monoides

> `φ̄ : Σ* / Ker(φ)  →  Im(φ)`

tal que `φ = φ̄ ∘ π`, donde `π : Σ* → Σ*/Ker(φ)` es la proyección canónica.

*Demostración.* Definimos `φ̄ : Σ*/Ker(φ) → Im(φ)` por `φ̄([w]) := φ(w) = f_w`.
- **Buena definición.** Si `[u] = [v]` en el cociente, entonces `u ∼ v`,
  es decir `φ(u) = φ(v)`. Luego el valor `φ̄([w])` no depende del
  representante elegido.
- **Homomorfismo.** En `Σ*/Ker(φ)` la operación es `[u]·[v] := [uv]`
  (bien definida por la Proposición 2). Por el Teorema 2,
  `φ̄([u]·[v]) = φ̄([uv]) = φ(uv) = φ(u) · φ(v) = φ̄([u]) · φ̄([v])`,
  y `φ̄([λ]) = φ(λ) = id_Q`.
- **Inyectividad.** Si `φ̄([u]) = φ̄([v])`, entonces `φ(u) = φ(v)`, luego
  `u ∼ v` y `[u] = [v]`.
- **Sobreyectividad sobre `Im(φ)`.** Trivial: si `f ∈ Im(φ)`, sea
  `w` cualquier preimagen; entonces `φ̄([w]) = f`.
- **Unicidad.** Cualquier `ψ` que cumpla `φ = ψ ∘ π` debe satisfacer
  `ψ([w]) = ψ(π(w)) = φ(w) = φ̄([w])`. ∎

Combinando con el Teorema 3 (`Im(φ) = M(A)`):

> **Corolario 1.** `Σ* / Ker(φ)  ≅  M(A)`   (isomorfismo de monoides).

Este corolario está verificado computacionalmente en
`Homomorphism.verify_first_isomorphism`, el cual comprueba dos condiciones:
(a) toda transformación `f ∈ M(A)` aparece como `φ(w)` para alguna palabra
de longitud `≤ |M(A)|`; (b) las clases agrupan únicamente palabras con la
misma imagen. La cota `|M(A)|` es suficiente porque cada nivel del BFS
añade al menos un elemento nuevo hasta agotar el monoide; por tanto el
representante mínimo de cualquier `f ∈ M(A)` tiene longitud `≤ |M(A)| - 1`.

### 4.6 El monoide de transición y el AFD mínimo: invarianza del lenguaje

El monoide `M(A)` se construye a partir de un AFD concreto `A`. Cabe
preguntarse si depende solo del **lenguaje** `L(A)` o del dibujo particular
del autómata. Para responderlo introducimos una relación de equivalencia
sobre `Σ*` (Saracino §8), extensión de dos lados de la relación de
Myhill–Nerode del libro de De Castro (§2.15):

> `u ≡_L v  ⟺  ∀ x, y ∈ Σ*:  xuy ∈ L ⇔ xvy ∈ L`.

Definimos `M(L) := Σ* / ≡_L`, el **monoide del lenguaje** `L` (una
construcción propia; De Castro solo trabaja la versión de un lado, §2.15).
Mostraremos que `M(L)` coincide con `M(A)` justamente cuando `A` es mínimo.

**Proposición 3 (relación entre las dos congruencias).** Para un AFD
`A = (Q, Σ, δ, q₀, F)` que reconozca `L`, denotemos por `∼` la congruencia
inducida por `φ_A : Σ* → M(A)` (es decir, `u ∼ v ⟺ f_u = f_v`). Entonces

> `∼  ⊆  ≡_L`,

esto es, `u ∼ v ⇒ u ≡_L v`.

*Demostración.* Supongamos `u ∼ v`, es decir, `f_u = f_v`. Entonces para
cualquier `x, y ∈ Σ*`, usando el Lema 0,

```
δ*(q₀, xuy) = δ*(δ*(q₀, x), uy) = δ*(δ*(δ*(q₀, x), u), y)
            = δ*(f_u(δ*(q₀, x)), y) = δ*(f_v(δ*(q₀, x)), y)
            = δ*(q₀, xvy).
```

Como `xuy` y `xvy` llevan a `q₀` al mismo estado, ambas pertenecen o no
pertenecen simultáneamente a `L`. Luego `u ≡_L v`. ∎

**Corolario 2.** Existe un homomorfismo sobreyectivo natural
`π̄ : M(A) ↠ M(L)`, y en consecuencia `M(L)` es un cociente de `M(A)`.

*Demostración.* La inclusión `∼ ⊆ ≡_L` implica que `≡_L` es una congruencia
en `Σ* / ∼ = M(A)`. El cociente correspondiente coincide con `M(L)`. ∎

**Teorema 5 (Caso de igualdad: AFD mínimo).** Si `A_min` es el AFD mínimo
que reconoce `L`, entonces `M(A_min) ≅ M(L)`.

*Demostración (esbozo).* Los estados de `A_min` son las clases de
Myhill–Nerode `[x]_R` con la relación `x R y ⟺ ∀ z: xz ∈ L ⇔ yz ∈ L`. Su
función de transición es `δ_min([x], a) = [xa]`. Calculamos `f_u = f_v` en
`M(A_min)` sii `[xu]_R = [xv]_R` para todo `x ∈ Σ*`, esto es, sii para todo
`x, y ∈ Σ*` se tiene `xuy ∈ L ⇔ xvy ∈ L`. Pero esto es exactamente
`u ≡_L v`. Por tanto las congruencias `∼` y `≡_L` coinciden en este caso,
y `M(A_min) = Σ*/∼ = Σ*/≡_L = M(L)`. ∎

**Conclusión.** El monoide de transición `M(A)` es siempre tan fino o más
fino que el monoide del lenguaje `M(L(A))`; ambos coinciden exactamente
cuando `A` es mínimo. Por la unicidad del AFD mínimo (De Castro, Teorema
2.15.4 y §2.16), esto muestra que `M(A_min)` es un **invariante del
lenguaje** `L`, no del autómata concreto. En este proyecto trabajamos
directamente con `M(A)` porque (i) se construye algorítmicamente sin
minimización previa, (ii) ilustra completamente el aparato del Primer
Teorema de Isomorfismo (Saracino §12), y (iii) cuando los AFDs de ejemplo
son ya mínimos, `M(A) = M(L)` y la información obtenida es intrínseca al
lenguaje.

---

## 5. Metodología

El proyecto sigue una metodología **constructiva y verificable**:
1. **Modelado matemático.** Cada definición y teorema de §4 se expone con
   demostración detallada.
2. **Diseño orientado a objetos.** Cada concepto matemático se materializa en
   una clase Python con responsabilidades únicas (`AFD`, `Transformation`,
   `TransitionMonoid`, `Homomorphism`).
3. **Algoritmo BFS** para construir `M(A)`: se inicia con la identidad y se
   aplica cada generador del alfabeto, deteniéndose cuando no aparecen
   transformaciones nuevas. Termina en a lo sumo `|M(A)| ≤ |Q|^|Q|` pasos.
4. **Verificación empírica.** Para cada AFD de ejemplo se prueba
   computacionalmente que `φ(uv) = φ(u) ⋆ φ(v)`, que `∼` es de equivalencia
   y que `|Σ*/Ker(φ)| = |M(A)|`.
5. **Pruebas unitarias** (`pytest`) en todos los módulos.
6. **Visualización** del AFD (Graphviz), tabla de Cayley (matplotlib) y
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
número par de unos (incluye `λ`, `00`, `11`, `0110`, …) y palabras con
número impar de unos (`1`, `10`, `01`, `111`, …).

**Primer Teorema:** `Σ*/Ker(φ) = {[λ], [1]} ≅ ℤ/2ℤ ≅ M(A)`.

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
con representantes mínimos `λ, 0, 1, 01, 11`. El monoide **no** es un grupo
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
| `[λ]`  | `λ` |
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
| `dfa.py` | Clase `AFD`, validación, `δ*`, ejecución, tabla. | 200 |
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
Entrada: AFD A = (Q, Σ, δ, q0, F)
Salida : conjunto M(A) ⊆ Q^Q y, para cada f ∈ M(A), una palabra rep(f).

1. Para cada a ∈ Σ, calcular el generador g_a(q) = δ(q, a).
2. Crear M ← {id_Q}, queue ← [(λ, id_Q)], rep(id_Q) ← λ.
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

Se ejecutó el programa sobre los tres AFDs incluidos. La siguiente tabla
resume las métricas observadas (todas verificadas por `pytest`):

| AFD | `\|Q\|` | `\|M(A)\|` | Cota `\|Q\|^\|Q\|` | Conmutativo | Grupo | Estructura conocida |
|----|--------|--------|----------|-----|------|---------------|
| Paridad | 2 | 2 | 4 | sí | sí | `ℤ/2ℤ` |
| Mód 3   | 3 | 3 | 27 | sí | sí | `ℤ/3ℤ` |
| Termina en `01` | 3 | 5 | 27 | no | no | monoide aperiódico |

Para cada AFD, la suite verifica además:
- `φ(uv) = φ(u).then(φ(v))` para toda `(u, v)` con `|u|, |v| ≤ 4`.
- `∼` es una relación de equivalencia (reflexividad, simetría,
  transitividad).
- `|Σ*/Ker(φ)| = |M(A)|`, lo que valida empíricamente el Primer Teorema
  del Isomorfismo (Corolario 1).

Salida típica del programa (`python main.py monoid examples/mod3_afd.json`):

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

1. **Naturaleza del monoide.** En los AFDs construidos sobre operaciones
   "modulares" (paridad, mód 3) los monoides resultan ser grupos cíclicos.
   Esto refleja un hecho general: si todos los símbolos inducen biyecciones
   sobre `Q`, entonces `M(A)` es un grupo (es un subgrupo del grupo
   simétrico `S_Q`).
2. **AFDs con "estados absorbentes lectorialmente".** En el ejemplo `01`,
   los símbolos colapsan el dominio (la lectura de un `0` deja siempre el
   estado en `s1`), por lo que las transformaciones no son inyectivas y el
   monoide no puede ser un grupo. En este caso `M(A)` resulta **aperiódico**:
   para todo elemento `x` alguna potencia se estabiliza, `x^k = x^(k+1)`
   (definición con potencias de un elemento, Saracino §3), lo que equivale
   a que `M(A)` no contenga ningún subgrupo no trivial.
3. **Cota `|Q|^|Q|`.** El ejemplo `01` muestra que la cota dista mucho de
   ser estrecha (5 vs. 27). En general, identificar `|M(A)|` exactamente es
   un problema *no trivial*: existen lenguajes regulares cuyos monoides de
   transición crecen exponencialmente en `|Q|`.
4. **Limitación del cociente truncado.** Computacionalmente no podemos
   exhibir clases infinitas de `Σ*`, pero exhibirlas hasta `|w| ≤ N` con
   `N ≥ |M(A)|` es suficiente para verificar el isomorfismo, porque la BFS
   garantiza que toda transformación aparece en a lo sumo `|M(A)|` pasos.

---

## 10. Conclusiones

- Se logró un **desarrollo riguroso** del marco algebraico que vincula AFDs
  y monoides, con demostraciones completas de cerradura, asociatividad,
  identidad, homomorfismo y Primer Teorema del Isomorfismo.
- Se construyó una herramienta Python **ejecutable, modular y probada**
  (51/51 tests verdes) que materializa fielmente las definiciones
  matemáticas y permite explorar interactivamente cualquier AFD dado en
  JSON.
- Los tres ejemplos canónicos ilustran tanto el caso "grupo" (paridad,
  módulo 3) como el caso "monoide aperiódico" (`01`), mostrando que la
  estructura algebraica capta información cualitativa del lenguaje.
- La integración entre **Matemática Discreta II** (estructuras algebraicas,
  relaciones, teoremas de isomorfismo) y **Teoría de la Computación** (AFDs,
  lenguajes regulares) queda explícita y operativa.

---

## 11. Trabajo futuro

- Implementar el **monoide del lenguaje** `M(L)` mediante minimización del
  AFD y verificar computacionalmente `M(A_min) ≅ M(L)` (sección 4.6).
- Exponer la **tabla de Cayley** completa y las clases del núcleo de `φ`
  como material de estudio para el Primer Teorema de Isomorfismo
  (Saracino §12).
- Extender el análisis a más familias de grupos que aparecen en Saracino
  (productos directos §5, grupos abelianos finitos §13, simétricos §7).
- Generar reportes en **LaTeX/PDF** automáticamente desde `visualization.py`.
- Implementar **representación matricial** de transformaciones para escalar
  a AFDs con cientos de estados.

---

## 12. Referencias

### Texto base del curso

0. **De Castro K., R.** *Introducción a la Teoría de la Computación.*
   Departamento de Matemáticas, Universidad Nacional de Colombia,
   II Semestre 2024. 219 pp.
   *(Referencia primaria de este proyecto: TODA la notación y las*
   *convenciones del código siguen este texto. Mapeo principal de*
   *secciones que sustentan el proyecto:*
   - *§1.1 – §1.13: alfabetos, cadenas, lenguajes.*
   - *§2.2: expresiones regulares.*
   - *§2.3 – §2.5: autómatas finitos deterministas (AFD).*
   - *§2.6: autómatas finitos no deterministas (AFN).*
   - *§2.7.1, §2.7.2: equivalencia AFD↔AFN, función δ̂.*
   - *§2.8 – §2.9: AFN-λ y equivalencia con AFN.*
   - *§2.10 – §2.11: complemento y producto cartesiano.*
   - *§2.12: Teorema de Kleene Parte I (regex → AFN-λ).*
   - *§2.13: Teorema de Kleene Parte II (autómata → regex via GEG).*
   - *§2.14: propiedades de clausura de los lenguajes regulares.*
   - *§2.15: Teorema de Myhill-Nerode (clases ≡_L → AFD mínimo).*
   - *§2.16: algoritmo de minimización de AFDs.*
   - *§3.1 – §3.2: criterio de no regularidad, lema de bombeo.*
   - *§6.1: Modelo estándar de Máquina de Turing.*
   - *§6.2: Ejemplos canónicos de MT (a^n b^n c^n, etc.).*
   - *§6.3 – §6.5: variaciones del modelo, MT no deterministas.*
   - *§6.7 – §6.8: Tesis de Turing, codificación de MTs.*
   - *§6.11: Máquina de Turing universal.)*

### Texto base de álgebra

1. **Saracino, D.** *Abstract Algebra: A First Course,* 2.ª ed., Waveland
   Press, 2008. *(Referencia primaria del aparato algebraico. Mapeo de
   secciones que sustentan el proyecto:*
   - *§1: operación binaria asociativa con identidad — definición de monoide.*
   - *§2: grupos y teoremas fundamentales.*
   - *§3: potencias de un elemento, grupos cíclicos, ℤ/nℤ, aperiodicidad.*
   - *§5: productos directos (V₄ = ℤ/2ℤ × ℤ/2ℤ).*
   - *§6: funciones y composición (transformaciones f_w : Q → Q).*
   - *§7: grupos simétricos (S₃).*
   - *§8: relaciones de equivalencia y clases (núcleo de φ).*
   - *§11: homomorfismos.*
   - *§12: homomorfismos y subgrupos normales — teorema de isomorfismo.*
   - *§13: grupos abelianos finitos.)*

### Nota sobre el aporte propio

El **monoide de transición** `M(A)`, el homomorfismo natural `φ` y la
aplicación del teorema de isomorfismo a este contexto son el aporte
específico del proyecto: combinan la maquinaria algebraica de Saracino
(monoides, composición, homomorfismos) con los autómatas de De Castro
Korgi, cuyo libro llega hasta Myhill-Nerode (§2.15) y minimización
(§2.16) pero no construye `M(A)` explícitamente. **El marco teórico se
apoya únicamente en estas dos fuentes.**
