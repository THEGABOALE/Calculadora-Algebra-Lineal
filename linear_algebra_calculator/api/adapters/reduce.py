"""
matrix/reduce: Gauss, Gauss-Jordan y Cramer sobre core/gauss.py,
core/gauss_jordan.py y core/cramer.py.

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

Cramer entra por acá y no por matrix/determinant: resuelve un sistema (pide A
y b), no calcula un determinante suelto. En matrix/determinant sigue
rechazado con 400 explícito -- ver el docstring de adapters/determinant.py.
Su respuesta difiere de la de gauss/gauss-jordan en dos puntos, ambos
deliberados y cubiertos por tests:

- `steps` es el envelope {frame:{states}}, no la lista plana. ResultPretty.tsx
  elige la rama de render por `input.method`, y para sarrus/cofactors/cramer
  lee `steps.frame.states` con estados autocontenidos.
- el `summary` no trae `rank`/`ranks`: la regla de Cramer no calcula rangos.
  Inventarlos exigiría devolver, bajo el rótulo de Cramer, un número que
  Cramer nunca produjo. La única excepción es interna a core/cramer.py: con
  det(A) = 0 y todos los det(Aᵢ) = 0 la regla no decide y el motor clasifica
  por rangos (Rouché–Frobenius); esos rangos quedan en el paso `rank_check`
  del procedimiento, no en el `summary`, así el shape es el mismo siempre.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.cramer import CramerMethod
from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.system_solver.gauss_solver import analyze_argumented, solve_from_upper
from utils.EquationFunctions import format_number, num_to_sub

from .frame import frame_to_states_envelope, frame_to_steps

Matrix = List[List[float]]

METODOS = ("gauss", "gauss-jordan", "cramer")


def _summary(final_matrix: Matrix, pivots) -> Dict[str, Any]:
    # tol=None: cero EXACTO. La eliminación de GaussMethod / GaussJordanMethod
    # ya decidió qué es ruido de redondeo (criterio de core/matrix_tools.py) y
    # lo dejó en 0.0; volver a mirar la matriz final con un umbral propio
    # (antes, 1e-12 absoluto) podía contradecir al motor: "0 = 1e-13" salía
    # compatible en la API aunque el sistema fuera incompatible.
    info = analyze_argumented(final_matrix, tol=None)
    solved = solve_from_upper(final_matrix, pivots=pivots, tol=None)

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


def _cramer_determinants(solver: CramerMethod, det_a: float) -> List[Dict[str, Any]]:
    """Los n+1 determinantes de la regla: det(A) y un det(Aᵢ) por variable.

    `CramerMethod.solve()` no devuelve los n determinantes de Cramer en el
    resultado, pero los deja en `solver.determinants_C` tal como los decidió:
    0.0 exacto cuando Aᵢ es numéricamente singular (rango < n), aunque la
    aritmética haya dado ruido de redondeo como 1e-17. Se toman de ahí y no
    se recalculan: recalcularlos con `calculate_determinant` devolvería ese
    ruido y la respuesta mostraría un det(Aᵢ) ≠ 0 justo en el caso en que el
    procedimiento dice que vale 0.

    Es el dato que la Fase 7 tiene que hacer llegar hasta el navegador: el
    frontend heredado mostraba UN determinante para Cramer, que es
    exactamente lo que Cramer no es.
    """
    determinants: List[Dict[str, Any]] = [
        {
            "variable": None,
            "label": "det(A)",
            "value": det_a,
            "value_pretty": format_number(det_a),
            "matrix": [row[:] for row in solver.matrix_A],
        }
    ]

    for col in range(solver.n_variables):
        C = solver.create_cramer_matrix(col)
        det_c = solver.determinants_C[col]
        determinants.append(
            {
                "variable": col,
                "label": f"det(A{num_to_sub(col + 1)})",
                "value": det_c,
                "value_pretty": format_number(det_c),
                "matrix": C,
            }
        )

    return determinants


def _cramer_summary(resultado: Dict[str, Any]) -> Dict[str, Any]:
    # Ya no normaliza nada: CramerMethod.solve() devuelve 'solution',
    # 'basic_vars' y 'free_vars' correctos de origen en las tres ramas --
    # None/[]/[] sin solución única, la lista/list(range(n))/[] con única.
    # (Antes esto forzaba esos tres campos con un ternario porque el motor
    # devolvía basic_vars=[0..n-1] en las ramas singulares y el literal
    # 'Crammer' como 'solution' en la de infinitas; los dos se corrigieron en
    # core/cramer.py.) Este adaptador sólo arma el shape que espera el
    # contrato web: 'variables' anidado, 'determinant_pretty' y 'is_singular'.
    status = resultado["status"]
    unica = status == "unique"
    det_a = resultado["determinant"]

    return {
        "status": status,
        "solution_type": status,
        "solution": resultado["solution"],
        "basic_vars": resultado["basic_vars"],
        "free_vars": resultado["free_vars"],
        "variables": {"basic": resultado["basic_vars"], "free": resultado["free_vars"]},
        "determinant": det_a,
        "determinant_pretty": format_number(det_a),
        "is_singular": not unica,
    }


def _matrix_cramer(A: Matrix, b: List[float]) -> Dict[str, Any]:
    # CramerMethod.__init__ levanta ValueError si b no acompaña a A o si la
    # matriz no es cuadrada; la vista lo traduce a 400 con el mensaje del
    # motor. No se duplica ninguno de esos dos chequeos en el serializer.
    solver = CramerMethod([row[:] for row in A], list(b))
    resultado = solver.solve()

    return {
        "input": {"method": "cramer", "A": A, "b": b},
        "steps": frame_to_states_envelope(solver.frame),
        "result": {
            "determinant": resultado["determinant"],
            "determinant_pretty": format_number(resultado["determinant"]),
            "determinants": _cramer_determinants(solver, resultado["determinant"]),
        },
        "summary": _cramer_summary(resultado),
    }


def matrix_reduce(*, method: str, A: Matrix, b: List[float]) -> Dict[str, Any]:
    if method == "cramer":
        return _matrix_cramer(A, b)

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
