"""
matrix/properties: rango, singularidad y núcleo sobre core/matrix_tools.py.

Endpoint aparte de matrix/operate, no un `operation` más: las 7 operaciones
de ese endpoint devuelven una matriz (`result.matrix`/`matrix_pretty`); esto
devuelve tres datos escalares/pequeños de una matriz, no una matriz -- no
encaja en ese shape y forzarlo ahí sería más confuso que un endpoint propio.

`rank_of` y `nullspace_vector` no exigen A cuadrada (funcionan sobre
rectangulares); `is_singular` sólo está definida para cuadradas y devuelve
None si no lo es -- ese None se propaga tal cual, no se fuerza a False ni se
rechaza en el serializer. Es la misma regla del resto de la API: la forma
(A es una matriz no vacía) se valida en serializers.py, lo matemático
(cuadrada o no, singular o no) lo decide core/.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.matrix_tools import is_singular, nullspace_vector, rank_of
from utils.EquationFunctions import format_number

Matrix = List[List[float]]


def matrix_properties(*, A: Matrix) -> Dict[str, Any]:
    rank = rank_of(A)
    singular = is_singular(A)
    nullspace = nullspace_vector(A)

    nullspace_pretty: Optional[List[str]] = (
        [format_number(v) for v in nullspace] if nullspace is not None else None
    )

    return {
        "input": {"operation": "properties", "A": A},
        "result": {
            "rank": rank,
            "is_singular": singular,
            "nullspace": nullspace,
            "nullspace_pretty": nullspace_pretty,
        },
    }
