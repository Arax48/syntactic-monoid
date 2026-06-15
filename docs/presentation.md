<!--
Presentación del proyecto.
Formato Marp / Pandoc-Beamer / reveal.js compatible (separador `---`).
16 diapositivas, ~12 minutos de exposición.
-->

# Estudio Algebraico de Autómatas Finitos Deterministas mediante Monoides de Transición

### Implementación computacional en Python

Matemática Discreta II · Teoría de la Computación
2026 — Semestre 1

---

## Diapositiva 1 — Motivación

- La teoría clásica de autómatas trata los AFDs como objetos **combinatorios**.
- El enfoque **algebraico** (Schützenberger, Eilenberg, Pin, Straubing)
  asocia a cada AFD un **monoide finito** cuya estructura captura el
  comportamiento del autómata.
- Pregunta central: **¿qué información sobre un AFD o un lenguaje regular
  puede leerse en la estructura algebraica de su monoide de transición?**

---

## Diapositiva 2 — Objetivos

1. Formalizar `M(A)` y demostrar que es un monoide.
2. Definir el homomorfismo natural `φ : Σ* → M(A)` y probar su propiedad
   morfística.
3. Caracterizar el núcleo `Ker(φ)` como congruencia de monoide.
4. Verificar el **Primer Teorema del Isomorfismo**:
   `Σ* / Ker(φ) ≅ M(A)`.
5. Implementar todo en Python con pruebas, ejemplos y visualización.

---

## Diapositiva 3 — Preliminares: monoide libre

- Alfabeto finito `Σ`, palabra `w = a₁…a_n`, longitud `|w| = n`.
- Concatenación asociativa con neutro `λ`:
  > `(Σ*, ·, λ)` es el **monoide libre**.
- Todo morfismo `Σ → M` se extiende de manera **única** a `Σ* → M`.

---

## Diapositiva 4 — AFD y transición extendida

`A = (Q, Σ, δ, q₀, F)` con `δ : Q × Σ → Q` total.

Función de transición extendida:

> `δ*(q, λ) = q`,    `δ*(q, wa) = δ(δ*(q, w), a)`.

Lenguaje aceptado:

> `L(A) = { w ∈ Σ* : δ*(q₀, w) ∈ F }`.

---

## Diapositiva 5 — Transformación inducida por una palabra

Para cada `w ∈ Σ*`:

> `f_w : Q → Q,    f_w(q) = δ*(q, w)`.

**Convención (composición diagramática).** `f · g := g ∘ f`.

**Lema clave** (usando el Lema 0 `δ*(q, uv) = δ*(δ*(q,u), v)`):

> `f_{uv} = f_u · f_v   =   f_v ∘ f_u`.

Cuidado con el **orden**: como leemos izquierda a derecha, primero se
aplica `f_u` y luego `f_v`.

---

## Diapositiva 6 — El monoide `M(A)`

`M(A) := { f_w : w ∈ Σ* } ⊆ Q^Q`.

| Propiedad | Justificación |
|----------|---------------|
| Cerrado bajo `·` | `f_u · f_v = f_{uv} ∈ M(A)` |
| Asociativa | Asociatividad de la composición de funciones |
| Identidad | `id_Q = f_λ ∈ M(A)` |

⇒ `(M(A), ·, id_Q)` es un **monoide finito** con `|M(A)| ≤ |Q|^|Q|`.

---

## Diapositiva 7 — Homomorfismo natural `φ`

`φ : (Σ*, ·, λ) → (M(A), ·, id_Q)`,  `φ(w) = f_w`.

> `φ(uv) = φ(u) · φ(v)`   y   `φ(λ) = id_Q`.

⇒ `φ` es homomorfismo **sobreyectivo** de monoides.

En el código: `phi(u).then(phi(v)) == phi(u + v)`.

---

## Diapositiva 8 — Núcleo y relación `∼`

> `u ∼ v   ⟺   φ(u) = φ(v)   ⟺   ∀ q ∈ Q:  δ*(q, u) = δ*(q, v)`.

Propiedades:
- **Reflexiva**, **simétrica**, **transitiva** ⇒ relación de equivalencia.
- **Compatible con la concatenación** ⇒ congruencia de monoide.

⇒ `Ker(φ) := ∼` particiona `Σ*` en clases compatibles con `·`.

---

## Diapositiva 9 — Primer Teorema del Isomorfismo

> `Σ* / Ker(φ)  ≅  M(A)`.

Esquema de la prueba:
1. `φ̄([w]) := φ(w)` está bien definida (independiente del representante).
2. Es morfismo de monoides.
3. Inyectiva por la definición de `∼`.
4. Sobreyectiva sobre `Im(φ) = M(A)`.
5. Única.

---

## Diapositiva 10 — Ejemplo 1: paridad

`Σ = {0,1}`, `Q = {Par, Impar}`, aceptación: paridad par.

- `f_0 = id`,  `f_1 = swap`.
- `M(A) = { id, swap } ≅ ℤ/2ℤ`.

Tabla de Cayley:

|   | e | 1 |
|---|---|---|
| **e** | e | 1 |
| **1** | 1 | e |

Clases de `∼`: palabras con `|w|_1` par vs. impar.

---

## Diapositiva 11 — Ejemplo 2: módulo 3

`Q = {r0, r1, r2}`, `f_0 = id`, `f_1 = (r0→r1→r2→r0)`.

- `M(A) = {id, f_1, f_1²} ≅ ℤ/3ℤ`.
- Tres clases en `Σ*/∼`: cantidad de unos mód 3.

|     | e | 1 | 11 |
|-----|---|---|----|
| **e**  | e  | 1  | 11 |
| **1**  | 1  | 11 | e  |
| **11** | 11 | e  | 1  |

---

## Diapositiva 12 — Ejemplo 3: termina en `01`

`Q = {s0, s1, s2}`, aceptación: `{s2}`.

`|M(A)| = 5`, generadores `f_0, f_1`.

```
    |  e   0   1   01  11
----+--------------------
e   |  e   0   1   01  11
0   |  0   0   01  01  11
1   |  1   0   11  01  11
01  |  01  0   11  01  11
11  |  11  0   11  01  11
```

No es grupo, no es conmutativo ⇒ refleja **aperiodicidad** del lenguaje.

---

## Diapositiva 13 — Arquitectura del software

```
syntactic-monoid/
├── dfa.py                 AFD, δ*, validación
├── transformation.py      f : Q → Q, composición, hash
├── transition_monoid.py   BFS, Cayley, identidad, |M(A)|
├── algebra.py             φ, Ker(φ), cociente, isomorfismo
├── visualization.py       Graphviz, matplotlib, reportes
├── main.py                CLI (10 opciones) + argparse
├── examples/              3 AFDs en JSON
└── tests/                 51 pruebas pytest
```

---

## Diapositiva 14 — Algoritmo BFS para `M(A)`

```
M ← { id_Q };  queue ← [(λ, id_Q)];  rep(id_Q) ← λ
mientras queue no vacía:
    (w, f) ← queue.popleft()
    para a ∈ Σ en orden:
        h ← f.then(g_a)          # h = f_{wa}
        si h ∉ M:
            M.add(h); rep(h) ← w·a; queue.append((w·a, h))
```

Termina en `O(|Σ| · |M(A)| · |Q|)` pasos; cota `|M(A)| ≤ |Q|^|Q|`.

---

## Diapositiva 15 — Resultados y verificación

51/51 pruebas pytest en verde:

- Validación estructural del AFD.
- Asociatividad / identidad de `Transformation`.
- Cerradura, asociatividad y cota `|Q|^|Q|` del monoide.
- `φ(uv) = φ(u).then(φ(v))` para `|u|, |v| ≤ 4`.
- `|Σ*/Ker(φ)| = |M(A)|` (Primer Teorema verificado empíricamente).
- Reflexividad / simetría / transitividad de `∼`.

CLI funcional con menú de 10 opciones e impresión de tablas y figuras.

---

## Diapositiva 16 — Conclusiones y trabajo futuro

**Logros**
- Demostraciones completas del marco algebraico AFD ↔ monoide.
- Implementación modular, probada y ejecutable.
- Tres ejemplos ilustran el caso "grupo" y el caso "aperiódico".

**Trabajo futuro**
- Monoide sintáctico `M(L)` vía minimización.
- Detección automática de aperiodicidad (libertad de estrella).
- Extensión a transductores y autómatas con salida.
- Caracterizaciones algebraicas dentro de la jerarquía de Eilenberg.

**¡Gracias!**
