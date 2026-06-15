"""
backend.models
==============

Modelos formales de computacion segun el libro de Rodrigo De Castro:
AFD (§2.3), AFN/AFN-λ (§2.6-2.8), AFP (§4.1), MT (§6.1), y la clase
auxiliar Transformation para el monoide de transicion.
"""

from backend.models.afd import AFD, AFDValidationError
from backend.models.transformation import Transformation
from backend.models.afn import AFN, AFNValidationError, LAMBDA
from backend.models.mt import (
    MT,
    BLANCO,
    CintaBidireccional,
    Desplazamiento,
    MTValidationError,
    ResultadoMT,
    TransicionMT,
)

__all__ = [
    "AFD",
    "AFDValidationError",
    "Transformation",
    "AFN",
    "AFNValidationError",
    "LAMBDA",
    "MT",
    "BLANCO",
    "CintaBidireccional",
    "Desplazamiento",
    "MTValidationError",
    "ResultadoMT",
    "TransicionMT",
]
