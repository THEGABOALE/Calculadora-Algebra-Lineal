"""
matrix/determinant: Sarrus y cofactores sobre core/cramer.py.

`CramerMethod.__init__(matriz, b)` exige `b` incluso para calcular un
determinante -- lo usa sólo para el chequeo de longitud en el constructor,
`calculate_determinant_sarrus`/`_cofactors` no lo tocan. Se construye con un
vector `b` de relleno (nunca sale en la respuesta) en vez de tocar
CramerMethod para separar esa validación de construcción: cambiar la firma
del motor por conveniencia de un endpoint no es parte de esta fase.

`method=cramer` NO se implementa acá. Cramer resuelve sistemas -- necesita A
y b, y core/cramer.py es justamente CramerMethod.solve(), no un método de
determinante -- así que se rechaza con 400 explícito en el serializer en vez
de redirigirlo en silencio a cofactores, que es el alias falso que tenía el
repo del que se porta el frontend (determinant_cramer(A) era literalmente
`return determinant_cofactors(A)`, y el botón "Cramer" nunca mostraba un
Cramer real). Cramer se resuelve de verdad en adapters/reduce.py, que es
donde vive lo que resuelve sistemas; el rechazo de acá sigue en pie.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.cramer import CramerMethod
from utils.EquationFunctions import format_number

from .frame import frame_to_states_envelope

Matrix = List[List[float]]

METODOS = ("sarrus", "cofactors")


def matrix_determinant(*, method: str, A: Matrix) -> Dict[str, Any]:
    n = len(A)
    cramer = CramerMethod([row[:] for row in A], [1.0] * n)  # b de relleno, no usado

    if method == "sarrus":
        det = cramer.calculate_determinant_sarrus(A)
    elif method == "cofactors":
        det = cramer.calculate_determinant_cofactors(A)
    else:
        raise ValueError(f"Método desconocido: {method!r}")

    return {
        "input": {"method": method, "A": A},
        "steps": frame_to_states_envelope(cramer.frame),
        "result": {"determinant": det, "determinant_pretty": format_number(det)},
    }
