"""
backend.models.mt
=================

Maquina de Turing (MT) estandar segun §6.1 del libro de Rodrigo De Castro.

Una MT se define formalmente como una 6-tupla:

    M = (Q, q0, F, Σ, Γ, δ)

donde:
    Q   : conjunto finito de estados internos de la unidad de control.
    q0  : estado inicial, q0 ∈ Q.
    F   : conjunto de estados finales o de aceptacion, ∅ ≠ F ⊆ Q.
    Σ   : alfabeto de entrada.
    Γ   : alfabeto de cinta, Σ ⊆ Γ.
    δ   : Q × Γ□ → Q × Γ□ × {←, →, −}, FUNCION PARCIAL.

El simbolo blanco □ es externo: NO pertenece a Γ. Se denota
Γ□ = Γ ∪ {□}. Las casillas en blanco de la cinta contienen □.

Una instruccion δ(q, s) = (q', s', D) significa: estando en el estado q,
escaneando el simbolo s, la unidad de control sobre-escribe s por s',
cambia al estado q' y realiza el desplazamiento D ∈ {←, →, −}.

La cinta es infinita en AMBAS direcciones; la cadena de entrada se
coloca en una porcion cualquiera y las demas casillas estan en blanco.

Configuracion instantanea: secuencia u q v con u, v ∈ Γ□* y q ∈ Q,
que indica que la unidad de control esta en el estado q escaneando
el primer simbolo de v (o □ si v es vacio).

Paso computacional: u1 q u2 |─ v1 p v2.
Notacion |─* indica uno o mas pasos.

Lenguaje aceptado:

    L(M) = { u ∈ Σ* : q0 u |─* v p w, p ∈ F, v, w ∈ Γ□* }.

La MT se detiene al entrar a F (no se permiten transiciones desde F).
δ es funcion parcial: si δ no esta definida para una configuracion,
el procesamiento se aborta sin aceptar.

Familias de lenguajes (§6.1):
- L es Turing-aceptable    si ∃ MT M tal que L(M) = L.
- L es Turing-decidible    si ademas M se detiene con TODAS las cadenas
                           de entrada (no hay bucles infinitos sobre Σ*).

Todo lenguaje Turing-decidible es Turing-aceptable; el reciproco no
es valido en general (§6.10).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


BLANCO = "□"


class Desplazamiento(Enum):
    """Movimientos permitidos de la unidad de control (§6.1)."""
    DERECHA = "→"
    IZQUIERDA = "←"
    ESTACIONARIA = "−"


class ResultadoMT(Enum):
    """Resultado posible del procesamiento de una cadena por la MT."""
    ACEPTACION = "aceptacion"          # entro a un estado de F
    ABORTADO = "abortado"              # δ no definida en la configuracion actual
    BUCLE_INFINITO = "bucle_infinito"  # se excedio max_pasos


class MTValidationError(ValueError):
    """Se lanza cuando la definicion de una MT no es estructuralmente valida."""


# ----------------------------------------------------------------------
# Cinta bi-infinita
# ----------------------------------------------------------------------

class CintaBidireccional:
    """Cinta infinita en AMBAS direcciones (modelo estandar §6.1).

    La posicion del cabezal puede ser un entero cualquiera. Las
    casillas no escritas explicitamente contienen el simbolo blanco □.
    Internamente se usa un dict[int, str] para no preasignar memoria.
    """

    def __init__(self, entrada: str = "", blanco: str = BLANCO) -> None:
        self.blanco = blanco
        self._celdas: Dict[int, str] = {}
        for i, s in enumerate(entrada):
            self._celdas[i] = s
        self.cabezal: int = 0

    def leer(self) -> str:
        return self._celdas.get(self.cabezal, self.blanco)

    def escribir(self, simbolo: str) -> None:
        if simbolo == self.blanco:
            self._celdas.pop(self.cabezal, None)
        else:
            self._celdas[self.cabezal] = simbolo

    def desplazar(self, d: Desplazamiento) -> None:
        if d is Desplazamiento.DERECHA:
            self.cabezal += 1
        elif d is Desplazamiento.IZQUIERDA:
            self.cabezal -= 1
        # ESTACIONARIA: no se mueve

    def configuracion_instantanea(self, estado: str) -> str:
        """Devuelve la configuracion u q v como una sola cadena.

        Conforme a §6.1: las casillas en blanco a la izquierda de u y
        a la derecha de v se omiten (son infinitas pero implicitas).
        """
        if not self._celdas:
            # Solo casillas en blanco. Mostrar q □ en la posicion del cabezal.
            return f"{estado}{self.blanco}"
        izq = min(min(self._celdas.keys()), self.cabezal)
        der = max(max(self._celdas.keys()), self.cabezal)
        partes: List[str] = []
        for i in range(izq, self.cabezal):
            partes.append(self._celdas.get(i, self.blanco))
        partes.append(estado)
        for i in range(self.cabezal, der + 1):
            partes.append(self._celdas.get(i, self.blanco))
        return "".join(partes)

    def snapshot(self) -> Tuple[List[str], int, int]:
        """Devuelve (celdas, indice_izquierdo, posicion_cabezal_relativa).

        Util para animacion: incluye el cabezal y al menos una celda
        a cada lado.
        """
        if not self._celdas:
            return [self.blanco], 0, 0
        izq = min(min(self._celdas.keys()), self.cabezal)
        der = max(max(self._celdas.keys()), self.cabezal)
        celdas = [self._celdas.get(i, self.blanco) for i in range(izq, der + 1)]
        return celdas, izq, self.cabezal - izq


# ----------------------------------------------------------------------
# Transiciones y traza
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class TransicionMT:
    """Una instruccion δ(q, s) = (q', s', D) (§6.1)."""
    desde_estado: str
    lee: str        # simbolo en Γ□ (puede ser BLANCO)
    a_estado: str
    escribe: str    # simbolo en Γ□ (puede ser BLANCO)
    desplazamiento: Desplazamiento

    def __str__(self) -> str:
        return (
            f"δ({self.desde_estado}, {self.lee}) = "
            f"({self.a_estado}, {self.escribe}, {self.desplazamiento.value})"
        )


@dataclass
class PasoMT:
    """Un paso computacional de la MT, registrado para la traza/animacion."""
    numero: int
    estado: str
    configuracion: str   # u q v segun §6.1
    cabezal: int
    leido: str
    transicion: Optional[TransicionMT] = None


@dataclass
class ResultadoEjecucion:
    """Resultado completo del procesamiento de una cadena por la MT."""
    resultado: ResultadoMT
    pasos: int
    estado_final: str
    configuracion_final: str
    traza: List[PasoMT]


# ----------------------------------------------------------------------
# Maquina de Turing
# ----------------------------------------------------------------------

@dataclass
class MT:
    """Maquina de Turing estandar (modelo §6.1 de De Castro).

    La 6-tupla M = (Q, q0, F, Σ, Γ, δ) se representa por:

        estados             ~  Q
        estado_inicial      ~  q0
        estados_aceptacion  ~  F
        alfabeto_entrada    ~  Σ
        alfabeto_cinta      ~  Γ        (NO incluye BLANCO)
        transiciones        ~  δ        (lista; la lookup table se
                                         construye en __post_init__)

    Observaciones (§6.1):
    - F debe ser no vacio.
    - BLANCO (□) es un simbolo externo y NO debe pertenecer a Γ ni a Σ.
    - Las transiciones desde estados de aceptacion estan prohibidas
      porque la MT se detiene al ingresar a F.
    - δ es funcion parcial: ausencia de regla aplicable ⇒ procesamiento
      abortado (sin aceptar).
    """

    estados: Set[str]
    estado_inicial: str
    estados_aceptacion: Set[str]
    alfabeto_entrada: Set[str]
    alfabeto_cinta: Set[str]
    transiciones: List[TransicionMT]
    nombre: str = field(default="MT")

    def __post_init__(self) -> None:
        self.estados = set(self.estados)
        self.estados_aceptacion = set(self.estados_aceptacion)
        self.alfabeto_entrada = set(self.alfabeto_entrada)
        self.alfabeto_cinta = set(self.alfabeto_cinta)
        self._delta: Dict[Tuple[str, str], TransicionMT] = {}
        for t in self.transiciones:
            clave = (t.desde_estado, t.lee)
            if clave in self._delta:
                raise MTValidationError(
                    f"Transicion duplicada para δ({t.desde_estado!r}, {t.lee!r}); "
                    f"la funcion de transicion debe ser deterministica."
                )
            self._delta[clave] = t
        self.validate()

    def validate(self) -> None:
        """Verifica que la MT es estructuralmente correcta segun §6.1."""
        if not self.estados:
            raise MTValidationError("Q (estados) no puede ser vacio.")
        if self.estado_inicial not in self.estados:
            raise MTValidationError(
                f"El estado inicial {self.estado_inicial!r} no pertenece a Q."
            )
        if not self.estados_aceptacion:
            raise MTValidationError("F (estados de aceptacion) no puede ser vacio.")
        if not self.estados_aceptacion.issubset(self.estados):
            extra = self.estados_aceptacion - self.estados
            raise MTValidationError(
                f"F debe estar contenido en Q; estados de mas: {sorted(extra)!r}."
            )
        if BLANCO in self.alfabeto_cinta:
            raise MTValidationError(
                f"El simbolo blanco {BLANCO!r} es externo y NO debe pertenecer a Γ."
            )
        if BLANCO in self.alfabeto_entrada:
            raise MTValidationError(
                f"El simbolo blanco {BLANCO!r} no debe pertenecer a Σ."
            )
        if not self.alfabeto_entrada.issubset(self.alfabeto_cinta):
            faltan = self.alfabeto_entrada - self.alfabeto_cinta
            raise MTValidationError(
                f"Σ debe estar contenido en Γ; simbolos faltantes: {sorted(faltan)!r}."
            )
        gamma_caja = self.alfabeto_cinta | {BLANCO}
        for t in self.transiciones:
            if t.desde_estado not in self.estados:
                raise MTValidationError(
                    f"Estado de origen {t.desde_estado!r} no pertenece a Q."
                )
            if t.desde_estado in self.estados_aceptacion:
                raise MTValidationError(
                    f"No se permiten transiciones desde estados de aceptacion "
                    f"(§6.1): {t.desde_estado!r}."
                )
            if t.a_estado not in self.estados:
                raise MTValidationError(
                    f"Estado destino {t.a_estado!r} no pertenece a Q."
                )
            if t.lee not in gamma_caja:
                raise MTValidationError(
                    f"Simbolo leido {t.lee!r} no pertenece a Γ□."
                )
            if t.escribe not in gamma_caja:
                raise MTValidationError(
                    f"Simbolo escrito {t.escribe!r} no pertenece a Γ□."
                )

    # ------------------------------------------------------------------
    # Ejecucion
    # ------------------------------------------------------------------

    def ejecutar(
        self,
        entrada: str,
        max_pasos: int = 10000,
        registrar_traza: bool = True,
    ) -> ResultadoEjecucion:
        """Procesa una cadena de entrada u ∈ Σ*.

        Inicia en la configuracion q0 u y va aplicando δ hasta:
            - entrar a un estado de aceptacion (resultado: ACEPTACION),
            - alcanzar una configuracion sin δ definido (ABORTADO), o
            - exceder max_pasos (BUCLE_INFINITO; refleja en la practica
              que el problema de la detencion es indecidible).
        """
        for s in entrada:
            if s not in self.alfabeto_entrada:
                raise ValueError(
                    f"Simbolo {s!r} no pertenece al alfabeto de entrada Σ."
                )

        cinta = CintaBidireccional(entrada)
        estado = self.estado_inicial
        traza: List[PasoMT] = []

        for paso in range(max_pasos + 1):
            leido = cinta.leer()
            configuracion = cinta.configuracion_instantanea(estado)

            if registrar_traza:
                traza.append(PasoMT(
                    numero=paso,
                    estado=estado,
                    configuracion=configuracion,
                    cabezal=cinta.cabezal,
                    leido=leido,
                ))

            if estado in self.estados_aceptacion:
                return ResultadoEjecucion(
                    resultado=ResultadoMT.ACEPTACION,
                    pasos=paso,
                    estado_final=estado,
                    configuracion_final=configuracion,
                    traza=traza,
                )

            transicion = self._delta.get((estado, leido))
            if transicion is None:
                return ResultadoEjecucion(
                    resultado=ResultadoMT.ABORTADO,
                    pasos=paso,
                    estado_final=estado,
                    configuracion_final=configuracion,
                    traza=traza,
                )

            if registrar_traza and traza:
                traza[-1].transicion = transicion

            cinta.escribir(transicion.escribe)
            cinta.desplazar(transicion.desplazamiento)
            estado = transicion.a_estado

        configuracion = cinta.configuracion_instantanea(estado)
        return ResultadoEjecucion(
            resultado=ResultadoMT.BUCLE_INFINITO,
            pasos=max_pasos,
            estado_final=estado,
            configuracion_final=configuracion,
            traza=traza,
        )

    def acepta(self, palabra: str, max_pasos: int = 10000) -> bool:
        """True si la palabra es aceptada por la MT."""
        r = self.ejecutar(palabra, max_pasos, registrar_traza=False)
        return r.resultado is ResultadoMT.ACEPTACION

    # ------------------------------------------------------------------
    # Serializacion JSON
    # ------------------------------------------------------------------

    _ALIAS_DESPLAZAMIENTO = {
        "→": Desplazamiento.DERECHA,
        "R": Desplazamiento.DERECHA,
        "DERECHA": Desplazamiento.DERECHA,
        "←": Desplazamiento.IZQUIERDA,
        "L": Desplazamiento.IZQUIERDA,
        "IZQUIERDA": Desplazamiento.IZQUIERDA,
        "−": Desplazamiento.ESTACIONARIA,
        "-": Desplazamiento.ESTACIONARIA,
        "S": Desplazamiento.ESTACIONARIA,
        "ESTACIONARIA": Desplazamiento.ESTACIONARIA,
    }

    @classmethod
    def from_dict(cls, data: dict) -> "MT":
        """Construye una MT a partir de un diccionario.

        Esquema esperado:
            {
              "nombre": str,
              "estados": [str, ...],
              "estado_inicial": str,
              "estados_aceptacion": [str, ...],
              "alfabeto_entrada": [str, ...],
              "alfabeto_cinta": [str, ...],         # NO incluye □
              "transiciones": [
                {"desde": str, "lee": str, "a": str,
                 "escribe": str, "desplazamiento": "→"|"←"|"−"},
                ...
              ]
            }
        """
        transiciones: List[TransicionMT] = []
        for r in data.get("transiciones", []):
            d_str = str(r.get("desplazamiento", "→")).upper()
            if d_str not in cls._ALIAS_DESPLAZAMIENTO:
                raise ValueError(
                    f"Desplazamiento desconocido: {d_str!r}. "
                    f"Usa uno de {sorted(set(cls._ALIAS_DESPLAZAMIENTO.keys()))}."
                )
            transiciones.append(TransicionMT(
                desde_estado=r["desde"],
                lee=r["lee"],
                a_estado=r["a"],
                escribe=r["escribe"],
                desplazamiento=cls._ALIAS_DESPLAZAMIENTO[d_str],
            ))
        return cls(
            estados=set(data["estados"]),
            estado_inicial=data["estado_inicial"],
            estados_aceptacion=set(data["estados_aceptacion"]),
            alfabeto_entrada=set(data["alfabeto_entrada"]),
            alfabeto_cinta=set(data["alfabeto_cinta"]),
            transiciones=transiciones,
            nombre=data.get("nombre", "MT"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "MT":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "tipo": "MT",
            "estados": sorted(self.estados),
            "estado_inicial": self.estado_inicial,
            "estados_aceptacion": sorted(self.estados_aceptacion),
            "alfabeto_entrada": sorted(self.alfabeto_entrada),
            "alfabeto_cinta": sorted(self.alfabeto_cinta),
            "transiciones": [
                {
                    "desde": t.desde_estado,
                    "lee": t.lee,
                    "a": t.a_estado,
                    "escribe": t.escribe,
                    "desplazamiento": t.desplazamiento.value,
                }
                for t in self.transiciones
            ],
        }

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"MT(nombre={self.nombre!r}, |Q|={len(self.estados)}, "
            f"|F|={len(self.estados_aceptacion)}, "
            f"|Σ|={len(self.alfabeto_entrada)}, "
            f"|Γ|={len(self.alfabeto_cinta)}, "
            f"|δ|={len(self.transiciones)})"
        )


__all__ = [
    "MT",
    "TransicionMT",
    "PasoMT",
    "ResultadoEjecucion",
    "ResultadoMT",
    "Desplazamiento",
    "CintaBidireccional",
    "MTValidationError",
    "BLANCO",
]
