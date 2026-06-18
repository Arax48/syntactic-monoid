/* ====================================================================
 * web/shared/monoid.js
 *
 * Estructura algebraica del monoide de transición M(A) de un AFD,
 * portada de backend/algebra/* a JavaScript.
 *
 * Construye M(A) por BFS sobre transformaciones Q → Q, analiza:
 *   - orden |M(A)|, comparado con la cota |Q|^|Q|;
 *   - idempotentes, unidades, centro Z(M);
 *   - si es un grupo (todos los elementos invertibles), si es abeliano,
 *     si es cíclico (y su generador);
 *   - aperiodicidad de Schützenberger (lenguajes star-free);
 *   - clasificación a la clase canónica: ℤ/nℤ, V₄ = ℤ/2ℤ × ℤ/2ℤ,
 *     S₃, grupo abeliano/no-abeliano genérico, monoide aperiódico, etc.
 *
 * Convención de composición (igual que en backend/algebra/homomorphism.py):
 *
 *     (f · g)(q) = g(f(q))      "lectura izquierda-a-derecha"
 *
 * para que φ(uv) = φ(u) · φ(v) sea homomorfismo (no anti-).
 * ==================================================================== */

"use strict";

class Transformation {
  constructor(map) {
    this.map = map;
    this._key = null;
  }
  apply(q) { return this.map.get(q); }
  /* (this · other)(q) = other(this(q)) */
  then(other) {
    const m = new Map();
    for (const [k, v] of this.map) m.set(k, other.map.get(v));
    return new Transformation(m);
  }
  key() {
    if (this._key !== null) return this._key;
    const entries = [...this.map.entries()];
    entries.sort((a, b) => a[0] < b[0] ? -1 : (a[0] > b[0] ? 1 : 0));
    this._key = entries.map(([k, v]) => k + "→" + v).join("|");
    return this._key;
  }
  static identity(states) {
    const m = new Map();
    for (const q of states) m.set(q, q);
    return new Transformation(m);
  }
  static fromSymbol(afd, sym) {
    const m = new Map();
    for (const q of afd.states) m.set(q, afd.trans.get(q).get(sym));
    return new Transformation(m);
  }
}

/* Construye M(A) por BFS desde la identidad. Devuelve {elements, repr,
   keyToIdx, idIdx}.

   Lanza una excepción si el monoide excede maxSize (defensiva: la cota
   |Q|^|Q| crece muy rápido para |Q| > 6). */
function computeMonoid(afd, maxSize = 4096) {
  const elements = [];
  const repr = new Map();      // key → palabra representante (más corta)
  const keyToIdx = new Map();

  const id = Transformation.identity(afd.states);
  const idKey = id.key();
  elements.push(id);
  keyToIdx.set(idKey, 0);
  repr.set(idKey, "");

  const queue = [{ word: "", t: id }];
  const syms = [...afd.alphabet].sort();

  // Pre-computar f_a para cada símbolo del alfabeto.
  const fa = {};
  for (const s of syms) fa[s] = Transformation.fromSymbol(afd, s);

  while (queue.length) {
    const { word, t } = queue.shift();
    for (const s of syms) {
      const next = t.then(fa[s]);
      const k = next.key();
      if (!keyToIdx.has(k)) {
        if (elements.length >= maxSize) {
          throw new Error(
            `Monoide demasiado grande (>${maxSize} elementos). ` +
            `Cota teórica |Q|^|Q| = ${Math.pow(afd.states.size, afd.states.size)}.`
          );
        }
        const idx = elements.length;
        elements.push(next);
        keyToIdx.set(k, idx);
        repr.set(k, word + s);
        queue.push({ word: word + s, t: next });
      }
    }
  }

  return { elements, repr, keyToIdx, idIdx: 0 };
}

/* Analiza propiedades algebraicas de M(A). */
function analyzeMonoid(monoid) {
  const { elements, idIdx } = monoid;
  const n = elements.length;

  // Tabla de composición (n x n) — O(n² × |Q|).
  const compTable = [];
  const elemKey = elements.map(e => e.key());
  for (let i = 0; i < n; i++) {
    const row = new Array(n);
    for (let j = 0; j < n; j++) {
      row[j] = monoid.keyToIdx.get(elements[i].then(elements[j]).key());
    }
    compTable.push(row);
  }

  // Idempotentes: f² = f
  const idempotents = [];
  for (let i = 0; i < n; i++) {
    if (compTable[i][i] === i) idempotents.push(i);
  }

  // Unidades: ∃ j, i·j = j·i = id
  const units = [];
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (compTable[i][j] === idIdx && compTable[j][i] === idIdx) {
        units.push(i); break;
      }
    }
  }

  const isGroup = units.length === n;

  // Abeliano
  let isAbelian = true;
  for (let i = 0; i < n && isAbelian; i++) {
    for (let j = i + 1; j < n; j++) {
      if (compTable[i][j] !== compTable[j][i]) { isAbelian = false; break; }
    }
  }

  // Centro Z(M)
  const center = [];
  for (let i = 0; i < n; i++) {
    let conm = true;
    for (let j = 0; j < n; j++) {
      if (compTable[i][j] !== compTable[j][i]) { conm = false; break; }
    }
    if (conm) center.push(i);
  }

  // Cíclico (solo si es grupo): buscar generador.
  let isCyclic = false, cyclicGen = -1, cyclicGenWord = null;
  if (isGroup) {
    for (let g = 0; g < n; g++) {
      const orbit = new Set();
      let cur = idIdx;
      while (!orbit.has(cur) && orbit.size < n + 1) {
        orbit.add(cur);
        cur = compTable[cur][g];
      }
      if (orbit.size === n) {
        isCyclic = true; cyclicGen = g;
        cyclicGenWord = monoid.repr.get(elemKey[g]);
        break;
      }
    }
  }

  // Aperiódico: ∀ x, ∃ k tal que x^k = x^(k+1).
  // Iteramos powers: si en algún punto x^k = x^(k+1), está estabilizado.
  let isAperiodic = true;
  for (let i = 0; i < n && isAperiodic; i++) {
    let cur = i;
    let stab = false;
    for (let k = 0; k <= n + 2; k++) {
      const nxt = compTable[cur][i];
      if (nxt === cur) { stab = true; break; }
      cur = nxt;
    }
    if (!stab) isAperiodic = false;
  }

  // Clasificación
  let isoLabel;
  if (isGroup) {
    if (n === 1) isoLabel = "{e} (trivial)";
    else if (isCyclic) isoLabel = `ℤ/${n}ℤ (cíclico)`;
    else if (n === 4 && isAbelian) isoLabel = "V₄ = ℤ/2ℤ × ℤ/2ℤ (Klein)";
    else if (n === 6 && !isAbelian) isoLabel = "S₃ (simétrico de 3)";
    else if (n === 8 && !isAbelian) isoLabel = `grupo no abeliano de orden 8 (D₄ o Q₈)`;
    else if (isAbelian) isoLabel = `grupo abeliano de orden ${n}`;
    else isoLabel = `grupo no abeliano de orden ${n}`;
  } else if (isAperiodic) {
    isoLabel = `monoide aperiódico de orden ${n}`;
  } else {
    isoLabel = `monoide de orden ${n}`;
  }

  return {
    n, isGroup, isAbelian, isCyclic, cyclicGen, cyclicGenWord,
    isAperiodic, idempotents, units, center, isoLabel,
  };
}

window.computeMonoid = computeMonoid;
window.analyzeMonoid = analyzeMonoid;
