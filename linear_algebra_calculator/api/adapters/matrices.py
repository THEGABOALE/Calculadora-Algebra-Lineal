"""
matrix/operate: las 8 operaciones de core/matrix_tools.py.

Match directo (categoría (a) del mapa de portación): add, sub, scalar,
transpose, matmul, sum_many, sub_many, matmul_chain tienen en core/ la misma
función, el mismo nombre y la misma firma `-> Tuple[Matrix, str]` que el
frontend ya conoce -- la copia del otro repo salió de acá. Este adaptador
sólo empaqueta.

`inverse` es la excepción: acepta `frame=` y usa `core/matrix_tools.inverse`
con el frame-lista de core/. Ver adapters/frame.py para el mapeo a
step_states.

La validación de FORMA (dimensiones, tipos, presencia de campos) vive en
api/serializers.py. La validación MATEMÁTICA (dimensiones incompatibles que
el serializer no puede anticipar, matriz singular en inverse) vive en core/ y
llega hasta acá como ValueError -- la vista la traduce a 400. No se duplica
ninguna regla matemática en esta capa.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.matrix_tools import (
    add_matrices,
    inverse,
    matmul,
    matmul_chain,
    scalar_mult,
    sub_many,
    sub_matrices,
    sum_many,
    transpose,
)
from utils.EquationFunctions import format_number

from .frame import frame_to_step_states_envelope

Matrix = List[List[float]]


def _matrix_pretty(M: Matrix) -> List[List[str]]:
    return [[format_number(v) for v in row] for row in M]


def _steps_from_text(steps_text: str) -> List[str]:
    # Mismo criterio que el repo del que se portó el contrato del frontend:
    # steps.split('\n'), sin filtrar líneas vacías -- matmul_chain las usa
    # como separador entre bloques y el frontend las renderiza sin problema.
    return steps_text.split("\n") if isinstance(steps_text, str) else steps_text


def matrix_operate(
    *,
    operation: str,
    A: Optional[Matrix] = None,
    B: Optional[Matrix] = None,
    matrices: Optional[List[Matrix]] = None,
    scalar: Optional[float] = None,
) -> Dict[str, Any]:
    if operation == "add":
        C, steps_text = add_matrices(A, B)
        return {
            "input": {"operation": operation, "A": A, "B": B},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "sub":
        C, steps_text = sub_matrices(A, B)
        return {
            "input": {"operation": operation, "A": A, "B": B},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "scalar":
        # scalar_mult(alpha, A): el escalar va primero.
        C, steps_text = scalar_mult(scalar, A)
        return {
            "input": {"operation": operation, "A": A, "scalar": scalar},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "transpose":
        T, steps_text = transpose(A)
        return {
            "input": {"operation": operation, "A": A},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": T, "matrix_pretty": _matrix_pretty(T)},
        }

    if operation == "matmul":
        C, steps_text = matmul(A, B)
        return {
            "input": {"operation": operation, "A": A, "B": B},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "sum_many":
        C, steps_text = sum_many(matrices)
        return {
            "input": {"operation": operation, "matrices": matrices},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "sub_many":
        # sub_many(first, rest): la primera matriz resta el resto en cadena.
        C, steps_text = sub_many(matrices[0], matrices[1:])
        return {
            "input": {"operation": operation, "matrices": matrices},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "matmul_chain":
        C, steps_text = matmul_chain(matrices)
        return {
            "input": {"operation": operation, "matrices": matrices},
            "steps": _steps_from_text(steps_text),
            "result": {"matrix": C, "matrix_pretty": _matrix_pretty(C)},
        }

    if operation == "inverse":
        frame: List[Dict[str, Any]] = []
        Ainv, _ = inverse(A, frame=frame)
        return {
            "input": {"operation": operation, "A": A},
            "steps": frame_to_step_states_envelope(frame),
            "result": {"matrix": Ainv, "matrix_pretty": _matrix_pretty(Ainv)},
        }

    raise ValueError(f"Operación desconocida: {operation!r}")
