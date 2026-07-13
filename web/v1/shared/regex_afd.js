/* ====================================================================
 * web/shared/regex_afd.js
 *
 * Pipeline regex → AFN-λ → AFD → AFD mínimo, compartido por
 * regex_visualizer.html y mt_visualizer.html. Portado de
 * backend/language/regex.py.
 *
 * Define en el scope global:
 *   Empty, Lambda, Sym, CharCls, AnyCh, Uni, Cat, Kln  (AST)
 *   RegexParser
 *   collectAlphabet(node)
 *   NFABuilder
 *   compileThompson(node, b, alpha)            -- construye fragmento AFN-λ
 *   regexToNFA(pattern, alphaInput)            -- regex → AFN-λ
 *   lambdaClosure(afn, statesIter)
 *   move(afn, states, sym)
 *   afnToAfd(afn)                              -- AFD por subconjuntos
 *   minimizeAfd(afd)                           -- AFD mínimo
 *   afdAccepts(afd, word)
 *
 *   regexToAfdMin(pattern, alphaInput)         -- atajo: regex → AFD mínimo
 * ==================================================================== */

"use strict";

/* ----- AST ----- */
class Empty   {}
class Lambda  {}
class Sym     { constructor(c){ this.char = c; } }
class CharCls { constructor(chars){ this.chars = chars; } }
class AnyCh   {}
class Uni     { constructor(l,r){ this.left = l; this.right = r; } }
class Cat     { constructor(l,r){ this.left = l; this.right = r; } }
class Kln     { constructor(c){ this.child = c; } }

/* ----- Parser ----- */
class RegexParser {
  constructor(src){ this.src = src; this.pos = 0; }
  peek(){ return this.pos >= this.src.length ? null : this.src[this.pos]; }
  parse(){
    if (this.src === "") return new Lambda();
    const n = this.parseUnion();
    if (this.pos !== this.src.length) {
      throw new Error(`Caracter inesperado en posicion ${this.pos}: '${this.src[this.pos]}'`);
    }
    return n;
  }
  parseUnion(){
    let left = this.parseConcat();
    while (this.peek() === "|"){
      this.pos++;
      const right = this.parseConcat();
      left = new Uni(left, right);
    }
    return left;
  }
  parseConcat(){
    const nodes = [];
    while (this.pos < this.src.length && this.peek() !== ")" && this.peek() !== "|") {
      nodes.push(this.parseRepeat());
    }
    if (nodes.length === 0) return new Lambda();
    let r = nodes[0];
    for (let i = 1; i < nodes.length; i++) r = new Cat(r, nodes[i]);
    return r;
  }
  parseRepeat(){
    let atom = this.parseAtom();
    while (["*", "+", "?"].includes(this.peek())) {
      const op = this.src[this.pos]; this.pos++;
      if (op === "*") atom = new Kln(atom);
      else if (op === "+") atom = new Cat(atom, new Kln(atom));
      else atom = new Uni(atom, new Lambda());
    }
    return atom;
  }
  parseAtom(){
    const c = this.peek();
    if (c === null || [")", "|", "*", "+", "?"].includes(c)) {
      throw new Error(`Atomo invalido en posicion ${this.pos}: '${c}'`);
    }
    if (c === "(") {
      this.pos++;
      const inner = this.parseUnion();
      if (this.peek() !== ")") throw new Error("Falta ')' de cierre.");
      this.pos++;
      return inner;
    }
    if (c === "[") return this.parseCharClass();
    if (c === ".") { this.pos++; return new AnyCh(); }
    if (c === "\\") {
      this.pos++;
      if (this.pos >= this.src.length) throw new Error("Escape '\\' al final.");
      const esc = this.src[this.pos]; this.pos++;
      return new Sym(esc);
    }
    this.pos++;
    return new Sym(c);
  }
  parseCharClass(){
    this.pos++;  // consume '['
    const chars = new Set();
    while (this.peek() !== "]") {
      if (this.peek() === null) throw new Error("Clase de caracteres sin cerrar.");
      let c = this.src[this.pos]; this.pos++;
      if (c === "\\") {
        if (this.pos >= this.src.length) throw new Error("Escape '\\' al final en clase.");
        c = this.src[this.pos]; this.pos++;
      }
      if (this.peek() === "-" && this.pos + 1 < this.src.length && this.src[this.pos + 1] !== "]") {
        this.pos++;  // consume '-'
        let end = this.src[this.pos]; this.pos++;
        if (end === "\\") {
          if (this.pos >= this.src.length) throw new Error("Escape '\\' al final en rango.");
          end = this.src[this.pos]; this.pos++;
        }
        if (c.charCodeAt(0) > end.charCodeAt(0)) {
          throw new Error(`Rango invalido: '${c}'-'${end}'`);
        }
        for (let k = c.charCodeAt(0); k <= end.charCodeAt(0); k++) {
          chars.add(String.fromCharCode(k));
        }
      } else {
        chars.add(c);
      }
    }
    this.pos++;  // consume ']'
    if (chars.size === 0) throw new Error("Clase de caracteres vacia.");
    return new CharCls(chars);
  }
}

function collectAlphabet(node) {
  if (node instanceof Empty || node instanceof Lambda || node instanceof AnyCh) return new Set();
  if (node instanceof Sym) return new Set([node.char]);
  if (node instanceof CharCls) return new Set(node.chars);
  if (node instanceof Uni || node instanceof Cat) {
    const s = collectAlphabet(node.left);
    for (const x of collectAlphabet(node.right)) s.add(x);
    return s;
  }
  if (node instanceof Kln) return collectAlphabet(node.child);
  throw new Error("Nodo desconocido");
}

/* ----- AFN-λ por la construccion clasica ----- */
class NFABuilder {
  constructor(){
    this.states = new Set();
    this.trans  = new Map();   // state -> Map<sym, Set<state>>
    this.lam    = new Map();   // state -> Set<state>
    this.counter = 0;
  }
  fresh(){
    const name = `q${this.counter++}`;
    this.states.add(name);
    this.trans.set(name, new Map());
    this.lam.set(name, new Set());
    return name;
  }
  addLam(p, q){ this.lam.get(p).add(q); }
  addSym(p, a, q){
    if (!this.trans.get(p).has(a)) this.trans.get(p).set(a, new Set());
    this.trans.get(p).get(a).add(q);
  }
}

function compileThompson(node, b, alpha) {
  if (node instanceof Empty) {
    const s = b.fresh(), a = b.fresh();
    return [s, a];
  }
  if (node instanceof Lambda) {
    const s = b.fresh(), a = b.fresh();
    b.addLam(s, a);
    return [s, a];
  }
  if (node instanceof Sym) {
    if (!alpha.has(node.char)) {
      throw new Error(`El simbolo '${node.char}' no esta en el alfabeto. Agregalo en el campo "Alfabeto".`);
    }
    const s = b.fresh(), a = b.fresh();
    b.addSym(s, node.char, a);
    return [s, a];
  }
  if (node instanceof CharCls) {
    const s = b.fresh(), a = b.fresh();
    for (const c of node.chars) {
      if (!alpha.has(c)) throw new Error(`El simbolo '${c}' de la clase no esta en el alfabeto.`);
      b.addSym(s, c, a);
    }
    return [s, a];
  }
  if (node instanceof AnyCh) {
    const s = b.fresh(), a = b.fresh();
    for (const c of alpha) b.addSym(s, c, a);
    return [s, a];
  }
  if (node instanceof Cat) {
    const [s1, a1] = compileThompson(node.left,  b, alpha);
    const [s2, a2] = compileThompson(node.right, b, alpha);
    b.addLam(a1, s2);
    return [s1, a2];
  }
  if (node instanceof Uni) {
    const [s1, a1] = compileThompson(node.left,  b, alpha);
    const [s2, a2] = compileThompson(node.right, b, alpha);
    const s = b.fresh(), a = b.fresh();
    b.addLam(s, s1); b.addLam(s, s2);
    b.addLam(a1, a); b.addLam(a2, a);
    return [s, a];
  }
  if (node instanceof Kln) {
    const [si, ai] = compileThompson(node.child, b, alpha);
    const s = b.fresh(), a = b.fresh();
    b.addLam(s, si); b.addLam(s, a);
    b.addLam(ai, si); b.addLam(ai, a);
    return [s, a];
  }
  throw new Error("Nodo desconocido en Thompson");
}

function regexToNFA(pattern, alphaInput) {
  const ast = new RegexParser(pattern).parse();
  const inferred = collectAlphabet(ast);
  let alpha;
  if (!alphaInput || alphaInput.size === 0) {
    if (inferred.size === 0) {
      throw new Error("No se pudo inferir el alfabeto (la regex no tiene literales). Especifica el alfabeto, por ejemplo: 01");
    }
    alpha = inferred;
  } else {
    alpha = new Set([...alphaInput, ...inferred]);
  }
  const b = new NFABuilder();
  const [start, accept] = compileThompson(ast, b, alpha);
  return {
    states: b.states, alphabet: alpha,
    trans: b.trans, lam: b.lam,
    start, accepting: new Set([accept]),
  };
}

/* ----- Simulacion y conversion AFN→AFD→minimo ----- */

function lambdaClosure(afn, statesIter) {
  const closure = new Set(statesIter);
  const queue = [...closure];
  while (queue.length > 0) {
    const q = queue.shift();
    for (const t of afn.lam.get(q) || []) {
      if (!closure.has(t)) { closure.add(t); queue.push(t); }
    }
  }
  return closure;
}

function move(afn, states, sym) {
  const out = new Set();
  for (const q of states) {
    const tr = afn.trans.get(q);
    if (tr && tr.has(sym)) for (const t of tr.get(sym)) out.add(t);
  }
  return out;
}

function afnToAfd(afn) {
  const symbols = [...afn.alphabet].sort();
  const nameOf = ss => ss.length === 0 ? "∅" : "{" + ss.join(",") + "}";

  const states = new Set();
  const trans = new Map();
  const accepting = new Set();
  const seen = new Map();
  const queue = [];

  function visit(ssArr) {
    const name = nameOf(ssArr);
    if (seen.has(name)) return name;
    seen.set(name, ssArr);
    states.add(name);
    trans.set(name, new Map());
    if (ssArr.some(q => afn.accepting.has(q))) accepting.add(name);
    queue.push(ssArr);
    return name;
  }

  const startSorted = [...lambdaClosure(afn, [afn.start])].sort();
  const startName = visit(startSorted);

  while (queue.length > 0) {
    const ss = queue.shift();
    const name = nameOf(ss);
    for (const a of symbols) {
      const next = [...lambdaClosure(afn, move(afn, ss, a))].sort();
      const nextName = visit(next);
      trans.get(name).set(a, nextName);
    }
  }

  return {
    states, alphabet: new Set(afn.alphabet),
    trans, start: startName, accepting,
  };
}

function minimizeAfd(afd) {
  const symbols = [...afd.alphabet].sort();
  const accepting = new Set([...afd.accepting]);
  const nonAcc = new Set();
  for (const s of afd.states) if (!accepting.has(s)) nonAcc.add(s);
  let partition = [];
  if (accepting.size > 0) partition.push(accepting);
  if (nonAcc.size > 0)    partition.push(nonAcc);

  let changed = true;
  while (changed) {
    changed = false;
    const next = [];
    for (const block of partition) {
      const groups = new Map();
      for (const s of block) {
        const sig = symbols.map(a => {
          const t = afd.trans.get(s).get(a);
          return partition.findIndex(b => b.has(t));
        }).join(",");
        if (!groups.has(sig)) groups.set(sig, new Set());
        groups.get(sig).add(s);
      }
      if (groups.size > 1) changed = true;
      for (const g of groups.values()) next.push(g);
    }
    partition = next;
  }

  const blockOf = new Map();
  partition.forEach((block, i) => {
    for (const s of block) blockOf.set(s, i);
  });

  const newStates = new Set();
  const newTrans  = new Map();
  const newAcc    = new Set();
  partition.forEach((block, i) => {
    const name = `q${i}`;
    newStates.add(name);
    newTrans.set(name, new Map());
    const rep = block.values().next().value;
    for (const a of symbols) {
      const t = afd.trans.get(rep).get(a);
      newTrans.get(name).set(a, `q${blockOf.get(t)}`);
    }
    if (afd.accepting.has(rep)) newAcc.add(name);
  });

  return {
    states: newStates, alphabet: new Set(afd.alphabet),
    trans: newTrans, start: `q${blockOf.get(afd.start)}`,
    accepting: newAcc,
  };
}

function afdAccepts(afd, word) {
  let s = afd.start;
  for (const c of word) {
    if (!afd.alphabet.has(c)) throw new Error(`Simbolo '${c}' fuera del alfabeto`);
    s = afd.trans.get(s).get(c);
  }
  return afd.accepting.has(s);
}

/* ----- Atajo: regex → AFD minimo ----- */
function regexToAfdMin(pattern, alphaInput) {
  const afn = regexToNFA(pattern, alphaInput);
  const afd = afnToAfd(afn);
  return minimizeAfd(afd);
}
