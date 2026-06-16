"""
backend.language.regex
======================

Expresiones regulares y construccion regex → AFN-λ, segun §2.2 y §2.12
(Teorema de Kleene Parte I) del libro de De Castro.

Definicion recursiva de las expresiones regulares sobre un alfabeto Σ
(§2.2):

    (1) Expresiones regulares basicas:
        ∅ es una expresion regular y L[∅] = ∅.
        λ es una expresion regular y L[λ] = {λ}.
        a es una expresion regular y L[a] = {a}, para cada a ∈ Σ.

    (2) Si R y S son expresiones regulares, entonces:
        (R ∪ S) es una expresion regular y L[(R ∪ S)] = L[R] ∪ L[S].
        (RS)    es una expresion regular y L[(RS)]    = L[R] · L[S].
        (R)*    es una expresion regular y L[(R)*]    = L[R]*.

Donde L[R] denota el lenguaje representado por la expresion regular R.
Por la propiedad A+ = A* · A = A · A*, la clausura positiva + tambien
se permite (§2.2). Las potencias R^n (azucar de R...R, n veces) y la
asociatividad/distributividad usual tambien se admiten.

Precedencia (de mayor a menor, §2.2): *, ·, ∪.

Nota sobre la sintaxis concreta de entrada (ASCII): para facilitar la
escritura desde teclado, este modulo acepta '|' como sinonimo de '∪'.
La notacion del libro usa '∪'; las salidas usan ese simbolo en lo
posible.

AST inmutable: Empty, Lambda, Symbol, CharClass, AnyChar, Union,
Concat, Star. Cada nodo tiene `__str__` que recompone la expresion.

Parser recursivo descendente con sintaxis concreta:
    operadores:               '|', concatenacion implicita, '*', '+', '?'
    parentesis:               '(', ')'
    clases de caracteres:     '[abc]', rangos '[a-z]'
    comodin:                  '.' (union de todo Σ)
    escapes:                  '\\(' '\\*' '\\\\' ...

Conversion regex → AFN-λ (Teorema 2.12.1, Teorema de Kleene Parte I):
implementada por la "construccion de Thompson" (nombre clasico de
algoritmo). Cada constructor del AST se traduce a un fragmento de
AFN-λ con dos estados distinguidos (inicial y final). La conexion
recursiva preserva la equivalencia L(AFN) = L[R].

Conversion regex → AFD: composicion de regex → AFN-λ (§2.12) seguida
de la construccion de subconjuntos (§2.7.1).

Cota: para una expresion regular de tamano n, el AFN-λ resultante
tiene a lo sumo 2n estados y 4n transiciones; el AFD por subconjuntos
puede crecer hasta 2^(2n) estados en el peor caso (aunque para
regexes pedagogicas suele ser mucho mas pequeno).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Optional, Set, Tuple

from backend.models.afn import AFN


class RegexParseError(ValueError):
    """Se lanza cuando una expresion regular no es sintacticamente valida."""


# ----------------------------------------------------------------------
# AST
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class RegexNode:
    """Clase base abstracta para los nodos del AST."""


@dataclass(frozen=True)
class Empty(RegexNode):
    """Denota el lenguaje vacio ∅. No se produce por el parser, util como
    constructor programatico."""

    def __str__(self) -> str:
        return "∅"


@dataclass(frozen=True)
class Lambda(RegexNode):
    """Denota el lenguaje {λ}."""

    def __str__(self) -> str:
        return "λ"


@dataclass(frozen=True)
class Symbol(RegexNode):
    """Denota el lenguaje {a} con a un simbolo del alfabeto."""

    char: str

    def __str__(self) -> str:
        return _escape_if_special(self.char)


@dataclass(frozen=True)
class CharClass(RegexNode):
    """Denota el lenguaje {a_1, ..., a_k} para una clase de caracteres
    [a_1...a_k] (azucar sintactico para la union de simbolos)."""

    chars: FrozenSet[str]

    def __str__(self) -> str:
        return "[" + "".join(sorted(self.chars)) + "]"


@dataclass(frozen=True)
class AnyChar(RegexNode):
    """Comodin '.': denota el alfabeto completo (todos los simbolos)."""

    def __str__(self) -> str:
        return "."


@dataclass(frozen=True)
class Union(RegexNode):
    """Union L(left) ∪ L(right)."""

    left: RegexNode
    right: RegexNode

    def __str__(self) -> str:
        return f"{self.left}|{self.right}"


@dataclass(frozen=True)
class Concat(RegexNode):
    """Concatenacion L(left)·L(right)."""

    left: RegexNode
    right: RegexNode

    def __str__(self) -> str:
        return f"{_paren_if_union(self.left)}{_paren_if_union(self.right)}"


@dataclass(frozen=True)
class Star(RegexNode):
    """Clausura de Kleene L(child)*."""

    child: RegexNode

    def __str__(self) -> str:
        return f"{_paren_if_compound(self.child)}*"


_SPECIAL = frozenset("()|*+?[].\\")


def _escape_if_special(c: str) -> str:
    return "\\" + c if c in _SPECIAL else c


def _paren_if_union(node: RegexNode) -> str:
    return f"({node})" if isinstance(node, Union) else str(node)


def _paren_if_compound(node: RegexNode) -> str:
    if isinstance(node, (Union, Concat)):
        return f"({node})"
    return str(node)


def collect_alphabet(node: RegexNode) -> FrozenSet[str]:
    """Devuelve el conjunto de simbolos literales que aparecen en el AST.

    No incluye los simbolos generados por AnyChar (que dependen de un
    alfabeto externo). Util para inferir Sigma cuando el usuario no lo
    suministra explicitamente.
    """
    if isinstance(node, (Empty, Lambda, AnyChar)):
        return frozenset()
    if isinstance(node, Symbol):
        return frozenset({node.char})
    if isinstance(node, CharClass):
        return frozenset(node.chars)
    if isinstance(node, (Union, Concat)):
        return collect_alphabet(node.left) | collect_alphabet(node.right)
    if isinstance(node, Star):
        return collect_alphabet(node.child)
    raise TypeError(f"Nodo de AST desconocido: {type(node).__name__}")


# ----------------------------------------------------------------------
# Parser
# ----------------------------------------------------------------------

class _Parser:
    """Parser recursivo descendente con tres niveles de precedencia.

    Gramatica (precedencia de menor a mayor):

        union   ::=  concat ( '|' concat )*
        concat  ::=  repeat repeat*
        repeat  ::=  atom ( '*' | '+' | '?' )*
        atom    ::=  '(' union ')' | charclass | '.' | escape | literal

    La concatenacion vacia (cuando los dos lados son λ) y la union
    con un lado vacio (e.g. 'a|') producen un nodo Lambda en ese lugar,
    siguiendo la convencion estandar.
    """

    def __init__(self, src: str) -> None:
        self.src = src
        self.pos = 0

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def parse(self) -> RegexNode:
        if not self.src:
            return Lambda()
        node = self._parse_union()
        if self.pos != len(self.src):
            raise RegexParseError(
                f"Caracter inesperado en posicion {self.pos}: "
                f"{self.src[self.pos]!r}"
            )
        return node

    # ------------------------------------------------------------------
    # Niveles
    # ------------------------------------------------------------------

    def _parse_union(self) -> RegexNode:
        left = self._parse_concat()
        while self._peek() == "|":
            self.pos += 1
            right = self._parse_concat()
            left = Union(left, right)
        return left

    def _parse_concat(self) -> RegexNode:
        nodes: list[RegexNode] = []
        while self.pos < len(self.src) and self._peek() not in (")", "|"):
            nodes.append(self._parse_repeat())
        if not nodes:
            return Lambda()
        result = nodes[0]
        for n in nodes[1:]:
            result = Concat(result, n)
        return result

    def _parse_repeat(self) -> RegexNode:
        atom = self._parse_atom()
        while self._peek() in ("*", "+", "?"):
            op = self.src[self.pos]
            self.pos += 1
            if op == "*":
                atom = Star(atom)
            elif op == "+":
                # r+  ≡  r r*
                atom = Concat(atom, Star(atom))
            else:  # '?'
                # r?  ≡  r | λ
                atom = Union(atom, Lambda())
        return atom

    def _parse_atom(self) -> RegexNode:
        c = self._peek()
        if c is None or c in (")", "|", "*", "+", "?"):
            raise RegexParseError(
                f"Atomo invalido en posicion {self.pos}: {c!r}"
            )
        if c == "(":
            self.pos += 1
            inner = self._parse_union()
            if self._peek() != ")":
                raise RegexParseError("Falta ')' de cierre.")
            self.pos += 1
            return inner
        if c == "[":
            return self._parse_charclass()
        if c == ".":
            self.pos += 1
            return AnyChar()
        if c == "\\":
            self.pos += 1
            if self.pos >= len(self.src):
                raise RegexParseError("Escape '\\' al final de la expresion.")
            esc = self.src[self.pos]
            self.pos += 1
            return Symbol(esc)
        # literal
        self.pos += 1
        return Symbol(c)

    def _parse_charclass(self) -> RegexNode:
        assert self._peek() == "["
        self.pos += 1
        chars: Set[str] = set()
        while self._peek() != "]":
            if self._peek() is None:
                raise RegexParseError("Clase de caracteres sin cerrar.")
            c = self.src[self.pos]
            self.pos += 1
            if c == "\\":
                if self.pos >= len(self.src):
                    raise RegexParseError(
                        "Escape '\\' al final dentro de clase de caracteres."
                    )
                c = self.src[self.pos]
                self.pos += 1
            # Posible rango c-d?
            if (
                self._peek() == "-"
                and self.pos + 1 < len(self.src)
                and self.src[self.pos + 1] != "]"
            ):
                self.pos += 1  # consume '-'
                end = self.src[self.pos]
                self.pos += 1
                if end == "\\":
                    if self.pos >= len(self.src):
                        raise RegexParseError("Escape '\\' al final en rango.")
                    end = self.src[self.pos]
                    self.pos += 1
                if ord(c) > ord(end):
                    raise RegexParseError(
                        f"Rango invalido: {c!r}-{end!r}."
                    )
                for code in range(ord(c), ord(end) + 1):
                    chars.add(chr(code))
            else:
                chars.add(c)
        self.pos += 1  # consume ']'
        if not chars:
            raise RegexParseError("Clase de caracteres vacia.")
        return CharClass(frozenset(chars))

    # ------------------------------------------------------------------
    # Utilidad
    # ------------------------------------------------------------------

    def _peek(self) -> Optional[str]:
        if self.pos >= len(self.src):
            return None
        return self.src[self.pos]


def parse(pattern: str) -> RegexNode:
    """Compila una cadena con sintaxis regex al AST correspondiente."""
    return _Parser(pattern).parse()


# ----------------------------------------------------------------------
# Construccion de Thompson
# ----------------------------------------------------------------------

class _ThompsonBuilder:
    """Acumulador mutable para los estados y transiciones del AFN.

    Se reciclan los nombres q0, q1, q2, ... como en Thompson clasico.
    """

    def __init__(self) -> None:
        self.states: Set[str] = set()
        self.transitions: dict[str, dict[str, Set[str]]] = {}
        self.lambda_transitions: dict[str, Set[str]] = {}
        self._counter = 0

    def fresh(self) -> str:
        name = f"q{self._counter}"
        self._counter += 1
        self.states.add(name)
        self.transitions[name] = {}
        self.lambda_transitions[name] = set()
        return name

    def add_lambda(self, src: str, dst: str) -> None:
        self.lambda_transitions[src].add(dst)

    def add_symbol(self, src: str, sym: str, dst: str) -> None:
        self.transitions[src].setdefault(sym, set()).add(dst)


def _compile(
    node: RegexNode,
    builder: _ThompsonBuilder,
    alphabet: FrozenSet[str],
) -> Tuple[str, str]:
    """Devuelve (estado_inicial, estado_final) del fragmento AFN del nodo."""
    if isinstance(node, Empty):
        # ∅: dos estados sin transicion entre ellos; el final es inalcanzable.
        s = builder.fresh()
        a = builder.fresh()
        return s, a
    if isinstance(node, Lambda):
        s = builder.fresh()
        a = builder.fresh()
        builder.add_lambda(s, a)
        return s, a
    if isinstance(node, Symbol):
        if node.char not in alphabet:
            # No es un error: Thompson sigue construyendo, pero el simbolo
            # no estara en el alfabeto del AFN y la palabra que lo
            # contiene sera rechazada por el validador del AFN. Mejor
            # avisar al usuario explicitamente.
            raise ValueError(
                f"El simbolo {node.char!r} no esta en el alfabeto "
                f"{sorted(alphabet)!r}."
            )
        s = builder.fresh()
        a = builder.fresh()
        builder.add_symbol(s, node.char, a)
        return s, a
    if isinstance(node, CharClass):
        s = builder.fresh()
        a = builder.fresh()
        for c in node.chars:
            if c not in alphabet:
                raise ValueError(
                    f"El simbolo {c!r} de la clase no esta en el alfabeto."
                )
            builder.add_symbol(s, c, a)
        return s, a
    if isinstance(node, AnyChar):
        s = builder.fresh()
        a = builder.fresh()
        for c in alphabet:
            builder.add_symbol(s, c, a)
        return s, a
    if isinstance(node, Concat):
        s1, a1 = _compile(node.left, builder, alphabet)
        s2, a2 = _compile(node.right, builder, alphabet)
        builder.add_lambda(a1, s2)
        return s1, a2
    if isinstance(node, Union):
        s1, a1 = _compile(node.left, builder, alphabet)
        s2, a2 = _compile(node.right, builder, alphabet)
        s = builder.fresh()
        a = builder.fresh()
        builder.add_lambda(s, s1)
        builder.add_lambda(s, s2)
        builder.add_lambda(a1, a)
        builder.add_lambda(a2, a)
        return s, a
    if isinstance(node, Star):
        s_inner, a_inner = _compile(node.child, builder, alphabet)
        s = builder.fresh()
        a = builder.fresh()
        builder.add_lambda(s, s_inner)
        builder.add_lambda(s, a)
        builder.add_lambda(a_inner, s_inner)
        builder.add_lambda(a_inner, a)
        return s, a
    raise TypeError(f"Nodo de AST desconocido: {type(node).__name__}")


def regex_to_afn(
    pattern: str,
    alphabet: Optional[Iterable[str]] = None,
    name: Optional[str] = None,
) -> AFN:
    """Compila una regex a un λ-AFN via Thompson.

    Parametros
    ----------
    pattern : str
        Expresion regular en sintaxis concreta.
    alphabet : Iterable[str], opcional
        Alfabeto Sigma del AFN resultante. Si es None, se infiere a
        partir de los literales del patron. Si el patron contiene el
        comodin '.' o esta vacio, conviene pasar el alfabeto explicito.
    name : str, opcional
        Nombre legible para el AFN.

    Devuelve
    --------
    AFN : λ-AFN cuyo lenguaje es el de la expresion regular.
    """
    ast = parse(pattern)
    inferred = collect_alphabet(ast)
    if alphabet is None:
        sigma: FrozenSet[str] = inferred
        if not sigma:
            raise ValueError(
                "No se pudo inferir el alfabeto (la regex no contiene "
                "literales). Pase explicitamente `alphabet`."
            )
    else:
        sigma = frozenset(alphabet) | inferred
        if not sigma:
            raise ValueError("El alfabeto no puede ser vacio.")

    builder = _ThompsonBuilder()
    start, accept = _compile(ast, builder, sigma)
    return AFN(
        states=builder.states,
        alphabet=set(sigma),
        transitions=builder.transitions,
        lambda_transitions=builder.lambda_transitions,
        start=start,
        accepting={accept},
        name=name or f"AFN({pattern})",
    )


def regex_to_afd(
    pattern: str,
    alphabet: Optional[Iterable[str]] = None,
    name: Optional[str] = None,
):
    """Compila una regex directamente a un AFD: Thompson + construccion
    de subconjuntos. Util cuando solo interesa el AFD (por ejemplo para
    verificar equivalencia con un AFD del usuario).
    """
    from backend.models.afd import AFD  # import diferido para evitar ciclo

    afn = regex_to_afn(pattern, alphabet=alphabet, name=name)
    dfa = afn.to_afd()
    if name:
        dfa.name = name
    return dfa


__all__ = [
    "RegexNode",
    "Empty",
    "Lambda",
    "Symbol",
    "CharClass",
    "AnyChar",
    "Union",
    "Concat",
    "Star",
    "RegexParseError",
    "parse",
    "collect_alphabet",
    "regex_to_afn",
    "regex_to_afd",
]
