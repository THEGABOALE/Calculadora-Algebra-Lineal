"""
matrix/reduce: Gauss y Gauss-Jordan sobre core/gauss.py y core/gauss_jordan.py.

`GaussMethod.solve_and_log()` y `GaussJordanMethod.solve_and_log()` no
devuelven el mismo shape entre sí -- GaussJordan agrega parametric_solution,
tipo_sistema, dependencia, determinant, is_singular; Gauss devuelve sólo lo
que sale de solve_from_upper. En vez de heredar esa diferencia hacia la API,
el `summary` se calcula acá una sola vez, directo con
core/system_solver/gauss_solver.py (analyze_argumented + solve_from_upper)
sobre la matriz final de cualquiera de los dos métodos: mismo shape de
respuesta sin importar cuál se haya usado para resolver.

Se llama a solve_and_log() igual, por su efecto de lado: agrega al frame los
pasos de resumen (tipo de solución, variables básicas/libres) que el usuario
espera ver en el procedimiento.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.system_solver.gauss_solver import analyze_argumented, solve_from_upper

from .frame import frame_to_steps

Matrix = List[List[float]]

METODOS = ("gauss", "gauss-jordan")


def _summary(final_matrix: Matrix, pivots) -> Dict[str, Any]:
    info = analyze_argumented(final_matrix)
    solved = solve_from_upper(final_matrix, pivots=pivots)

    rank_a = info["rank"]
    # rank([A|b]): si el sistema es inconsistente, la columna de b aporta un
    # pivote más que A por sí sola; si no, coincide con rank(A).
    rank_ab = rank_a + (1 if info["inconsistent_rows"] else 0)

    return {
        "status": solved["status"],
        "solution_type": solved["status"],
        "solution": solved["solution"],
        "rank": rank_a,
        "ranks": {"rankA": rank_a, "rankAb": rank_ab},
        "basic_vars": solved["basic_vars"],
        "free_vars": solved["free_vars"],
        "variables": {"basic": solved["basic_vars"], "free": solved["free_vars"]},
        "inconsistent_rows": solved["inconsistent_rows"],
    }


def matrix_reduce(*, method: str, A: Matrix, b: List[float]) -> Dict[str, Any]:
    if method == "gauss":
        solver = GaussMethod([row[:] for row in A], list(b))
        solver.gauss_method()
        solver.solve_and_log()
    elif method == "gauss-jordan":
        solver = GaussJordanMethod([row[:] for row in A], list(b))
        solver.run()
        solver.solve_and_log()
    else:
        raise ValueError(f"Método desconocido: {method!r}")

    return {
        "input": {"method": method, "A": A, "b": b},
        "steps": frame_to_steps(solver.frame),
        "summary": _summary(solver.matriz, solver.pivots),
    }
