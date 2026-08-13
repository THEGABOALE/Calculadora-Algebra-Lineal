"""
numeric/{bisection-method, false-position, newton-raphson, secant}.

Los cuatro métodos existen en core/numeric/, pero ninguno de sus nombres de
campo coincide con lo que el frontend a portar espera -- se inspiraron en la
misma convención, no comparten vocabulario. Este adaptador hace los renames,
fila por fila y a nivel de resultado.

CRITERIO: biseccion y regla_falsa son los únicos que aceptan `criterio` en
core/ (newton y secante no tienen ese parámetro). Acá se fuerza siempre
criterio="intervalo" para esos dos -- nunca el default de core/
("error_relativo") -- porque el encabezado de columna del frontend dice
literalmente "xu-xi<E": mostrar un criterio distinto del que se usó sería
mentir en la tabla sin que nadie lo note. Newton y secante no tienen
equivalente: siguen con el único criterio que soportan (error relativo).

interval_length y Ea_lt_E son derivados, no datos que core/ calcule: se
computan acá a partir de lo que cada fila ya trae. interval_length sólo
aplica a biseccion/regla_falsa (son las únicas con a/b por fila); Ea_lt_E
aplica a los cuatro (siempre hay un error y una tolerancia con las que
compararlo, sea cual sea el criterio que efectivamente cortó el bucle).

GAP CONOCIDO, no resuelto acá: newton-raphson y secante en el frontend
referencian result.iterations_estimate con una forma propia
(formula_newton/formula_secant, formula_error_*, numeric.last_error) que
core/numeric/metodos_abiertos.py no calcula -- no hay una cota de
iteraciones de forma cerrada para esos métodos como sí la hay para
bisección (log2). Se deja sin poblar: el frontend usa `?.` en cada acceso,
así que esa sección queda vacía en vez de romper.

INFINITO: la primera fila de cada historial siempre trae error=inf (no hay
iteración anterior con la que compararlo). float('inf') no es JSON válido
-- DRF revienta con 500 al serializar, no es algo hipotético, se disparó al
verificar contra el endpoint real. Se sanea a None con _finito(): el
frontend ya trata null/undefined como "sin valor" (fmt() en cada *Inputs.tsx
devuelve '-' para ese caso), así que no hace falta inventar un contrato
nuevo, alcanza con no romper el que ya existe. Ea_lt_E se calcula ANTES de
sanear, sobre el float crudo: `inf < tolerancia` da False de forma natural,
sin necesitar un caso especial.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from core.numeric.metodos_abiertos import metodo_newton_raphson, metodo_secante
from core.numeric.metodos_cerrados import metodo_biseccion, metodo_regla_falsa

from .latex import latex_a_texto

CRITERIO_CERRADOS = "intervalo"


def _finito(x: float) -> Optional[float]:
    return x if math.isfinite(x) else None


def _estimacion(estimacion: Dict[str, Any]) -> Dict[str, Any]:
    lx = estimacion["latex"]
    return {
        "longitud_intervalo": estimacion["longitud_intervalo"],
        "tolerancia": estimacion["tolerancia"],
        "n_min": estimacion["n_minimo"],
        "latex": {
            "formula_general": lx["formula"],
            "formula_substitution": lx["sustitucion"],
            "formula_numeric": lx["numerico"],
            "n_min": estimacion["n_minimo"],
        },
    }


def _detalles(detalles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"iteration": d["iteracion"], "lines": d["lineas"]} for d in detalles]


def _conclusion(conclusion: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "latex": conclusion["latex"],
        "root": conclusion["raiz"],
        "iterations": conclusion["iteraciones"],
        "criterio_paro": conclusion["criterio_paro"],
    }


def _fila_cerrado(fila: Dict[str, Any], tolerancia: float) -> Dict[str, Any]:
    """Común a bisección y regla falsa: mismas claves de historial."""
    a, b, error = fila["a"], fila["b"], fila["error"]
    return {
        "iteration": fila["iteracion"],
        "xl": a,
        "xu": b,
        "xr": fila["xr"],
        "yl": fila["f(a)"],
        "yu": fila["f(b)"],
        "yr": fila["f(xr)"],
        "Ea": _finito(error),
        "interval_length": b - a,
        "Ea_lt_E": error < tolerancia,
    }


def _fila_newton(fila: Dict[str, Any], tolerancia: float) -> Dict[str, Any]:
    error = fila["error"]
    return {
        "iteration": fila["iteracion"],
        "xk": fila["x"],
        "fxk": fila["f(x)"],
        "fprimexk": fila["f'(x)"],
        "x_next": fila["x_nuevo"],
        "Ea": _finito(error),
        "Ea_lt_E": error < tolerancia,
    }


def _fila_secante(fila: Dict[str, Any], tolerancia: float) -> Dict[str, Any]:
    error = fila["error"]
    return {
        "iteration": fila["iteracion"],
        "x_prev": fila["x_{n-1}"],
        "x_curr": fila["x_n"],
        "x_next": fila["x_{n+1}"],
        "f_prev": fila["f(x_{n-1})"],
        "f_curr": fila["f(x_n)"],
        "f_next": fila["f(x_{n+1})"],
        "Ea": _finito(error),
        "Ea_lt_E": error < tolerancia,
    }


def _base(resultado: Dict[str, Any], tabla: List[Dict[str, Any]]) -> Dict[str, Any]:
    salida: Dict[str, Any] = {
        "table": tabla,
        "details": _detalles(resultado["detalles"]),
        "conclusion": _conclusion(resultado["conclusion"]),
        "function_latex": resultado["funcion_latex"],
        "root": resultado["raiz"],
        "iterations": resultado["iteraciones"],
        "error_final": _finito(resultado["error_final"]),
        "method": resultado["metodo"],
    }
    if "estimacion_iteraciones" in resultado:
        salida["iterations_estimate"] = _estimacion(resultado["estimacion_iteraciones"])
    if "advertencia" in resultado:
        salida["warning"] = resultado["advertencia"]
    if "derivada_latex" in resultado:
        salida["derivative_latex"] = resultado["derivada_latex"]
    return salida


def bisection_method(*, function_latex: str, xi: float, xu: float, tolerance: float, max_iter: int = 100) -> Dict[str, Any]:
    f_str = latex_a_texto(function_latex)
    resultado = metodo_biseccion(f_str, xi, xu, tolerance, criterio=CRITERIO_CERRADOS, max_iter=max_iter)
    tabla = [_fila_cerrado(fila, tolerance) for fila in resultado["historial"]]
    return _base(resultado, tabla)


def false_position_method(*, function_latex: str, xi: float, xu: float, tolerance: float, max_iter: int = 100) -> Dict[str, Any]:
    f_str = latex_a_texto(function_latex)
    resultado = metodo_regla_falsa(f_str, xi, xu, tolerance, criterio=CRITERIO_CERRADOS, max_iter=max_iter)
    tabla = [_fila_cerrado(fila, tolerance) for fila in resultado["historial"]]
    return _base(resultado, tabla)


def newton_raphson_method(*, function_latex: str, x0: float, tolerance: float, max_iter: int = 100) -> Dict[str, Any]:
    f_str = latex_a_texto(function_latex)
    resultado = metodo_newton_raphson(f_str, x0, tolerance, max_iter=max_iter)
    tabla = [_fila_newton(fila, tolerance) for fila in resultado["historial"]]
    return _base(resultado, tabla)


def secant_method(*, function_latex: str, x0: float, x1: float, tolerance: float, max_iter: int = 100) -> Dict[str, Any]:
    f_str = latex_a_texto(function_latex)
    resultado = metodo_secante(f_str, x0, x1, tolerance, max_iter=max_iter)
    tabla = [_fila_secante(fila, tolerance) for fila in resultado["historial"]]
    return _base(resultado, tabla)
