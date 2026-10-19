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

from core.numeric.errores import (
    calcular_error_absoluto_relativo,
    calcular_error_acumulado,
    texto_compacto,
    texto_exacto,
    texto_fijo,
    texto_operacion,
    texto_redondeado,
)
from core.numeric.metodos_abiertos import metodo_newton_raphson, metodo_secante
from core.numeric.propagacion import propagar_error, texto_preciso, texto_valor
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
    if "modo_angular" in resultado:
        # Campo nuevo y aditivo: el frontend no lo lee, pero deja explícito
        # en qué unidad están x0, x1, la tabla y la raíz.
        salida["angle_mode"] = resultado["modo_angular"]
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


def secant_method(*, function_latex: str, x0: float, x1: float, tolerance: float, max_iter: int = 100, angle_mode: str = "rad") -> Dict[str, Any]:
    f_str = latex_a_texto(function_latex)
    resultado = metodo_secante(f_str, x0, x1, tolerance, max_iter=max_iter, modo_angular=angle_mode)
    tabla = [_fila_secante(fila, tolerance) for fila in resultado["historial"]]
    return _base(resultado, tabla)


def abs_rel_error(*, true_value: str, approx_value: str, decimals_display: int) -> Dict[str, Any]:
    """numeric/abs-rel-error -- core/numeric/errores.py.

    Conserva las claves que lee ErrorAbsRelInputs.tsx (input.*_pretty y, en
    cada error, operation/formula/result) y agrega, sin romperlas:
    `exact` (el valor sin redondear), `percent`, `defined` y `note` en el
    relativo, y `decimals_display` en input. Los números van como texto:
    son Decimal y JSON no tiene cómo representarlos sin pasar por float.
    """
    r = calcular_error_absoluto_relativo(true_value, approx_value, decimals_display)
    ea, er = r["error_absoluto"], r["error_relativo"]
    m_txt = texto_exacto(r["valor_verdadero"])
    mt_txt = texto_exacto(r["valor_aproximado"])
    return {
        "input": {
            "true_value": m_txt,
            "approx_value": mt_txt,
            "true_value_pretty": m_txt,
            "approx_value_pretty": mt_txt,
            "decimals_display": r["decimales"],
        },
        "absolute_error": {
            "operation": {"numerator": ea["formula"]},
            "formula": {"numerator": ea["sustitucion"]},
            "result": ea["texto"],
            "exact": texto_exacto(ea["valor"]),
        },
        "relative_error": {
            "operation": {"numerator": er["formula"][0], "denominator": er["formula"][1]},
            "formula": {"numerator": er["sustitucion"][0], "denominator": er["sustitucion"][1]},
            "result": er["texto"],
            "exact": None if er["valor"] is None else texto_exacto(er["valor"]),
            "percent": er["porcentaje"],
            "defined": er["valor"] is not None,
            "note": er["nota"],
        },
    }


def error_accumulation(
    *,
    initial_amount: str,
    iterations: int,
    mode: str,
    rate: str,
    approx_decimals: int,
    interest_display_decimals: int,
) -> Dict[str, Any]:
    """numeric/error-accumulation -- core/numeric/errores.calcular_error_acumulado.

    Tres tipos de valor, con nombres distintos para no confundirlos:
    - `*_pretty` de la trayectoria aproximada: el valor exacto con
      approx_decimals decimales (ya está redondeado; mostrarlo no redondea).
    - `*_pretty` de la trayectoria real, diferencias y errores: redondeados a
      interest_display_decimals, con "≈" si no son el valor exacto.
    - `difference`, `error_accum`, `amount_real`, `local_error`,
      `propagated_error`: el valor exacto como texto decimal. Antes eran
      números en el frontend; con float se perdería justamente la precisión
      que se mide.

    `prev_amount_pretty` es el saldo aproximado anterior (al que se aplica la
    operación); el real anterior va en `prev_amount_real_pretty`.
    `summary.initial_amout_pretty` (sic) se conserva como alias de
    `initial_amount_pretty` para el frontend existente.
    """
    r = calcular_error_acumulado(initial_amount, rate, iterations, mode, approx_decimals)
    da, dp = approx_decimals, interest_display_decimals
    operacion = texto_operacion(mode, da)

    def aprox(v):
        return texto_fijo(v, da)

    def real(v):
        return texto_redondeado(v, dp)

    filas = []
    for f in r["filas"]:
        filas.append({
            "iteration": f["iteracion"],
            "prev_amount_pretty": aprox(f["monto_anterior_aprox"]),
            "prev_amount_approx_pretty": aprox(f["monto_anterior_aprox"]),
            "prev_amount_real_pretty": real(f["monto_anterior_real"]),
            "interest_real_pretty": real(f["interes_real"]),
            "interest_approx_pretty": aprox(f["interes_aprox"]),
            "amount_real_pretty": real(f["monto_real"]),
            "amount_real": texto_compacto(f["monto_real"]),
            "amount_approx_pretty": aprox(f["monto_aprox"]),
            "difference": texto_compacto(f["diferencia"]),
            "difference_pretty": real(f["diferencia"]),
            "local_error": texto_compacto(f["error_local"]),
            "local_error_pretty": real(f["error_local"]),
            "propagated_error": texto_compacto(f["error_propagado"]),
            "propagated_error_pretty": real(f["error_propagado"]),
            "error_accum": texto_compacto(f["error_acumulado"]),
            "error_accum_pretty": real(f["error_acumulado"]),
            "approx_mode": mode,
            "approx_operation_text": operacion,
        })

    resumen = r["resumen"]
    monto_inicial = texto_compacto(r["monto_inicial"])
    tasa = texto_compacto(r["tasa"])
    return {
        "input": {
            "initial_amount": monto_inicial,
            "iterations": iterations,
            "mode": mode,
            "rate": tasa,
            "approx_decimals": da,
            "interest_display_decimals": dp,
        },
        "data": {
            "rows": filas,
            "summary": {
                "iterations": iterations,
                "initial_amount_pretty": monto_inicial,
                "initial_amout_pretty": monto_inicial,
                "final_amount_real_pretty": real(resumen["monto_final_real"]),
                "final_amount_approx_pretty": aprox(resumen["monto_final_aprox"]),
                "final_error_accum": texto_compacto(resumen["error_acumulado_final"]),
                "final_error_accum_pretty": real(resumen["error_acumulado_final"]),
                "rate": tasa,
                "rate_percent": f"{texto_compacto(r['tasa'] * 100)} %",
                "mode": mode,
                "approx_operation_text": operacion,
            },
        },
    }


def _tex_numero(texto: str) -> str:
    """Texto de presentación -> LaTeX: "≈ 1.5E-7" -> "1.5 \times 10^{-7}"."""
    t = texto[2:] if texto.startswith("≈ ") else texto
    if "E" in t:
        mantisa, exponente = t.split("E")
        t = rf"{mantisa} \times 10^{{{int(exponente)}}}"
    return t


def _relacion(texto: str) -> str:
    return r"\approx" if texto.startswith("≈") else "="


def _entre_parentesis(tex: str) -> str:
    return rf"\left({tex}\right)" if tex.startswith("-") else tex


def _tex_valor_exacto(valor, par) -> str:
    """Un dato de entrada (x0, Δx, x0+Δx): decimal si es exacto, si no LaTeX."""
    from sympy import latex

    decimal, exacto = par
    return texto_compacto(decimal) if exacto else latex(valor)


def propagation_error(
    *,
    function_latex: str,
    x0: str,
    delta_x: str,
    angle_mode: str = "rad",
    decimals: int = 6,
) -> Dict[str, Any]:
    """numeric/propagation-error -- core/numeric/propagacion.py.

    function_latex, x0 y delta_x llegan como LaTeX de MathQuill y se
    traducen con el parser estricto (el de calculus/derivate). Conserva las
    claves que lee PropagationErrorInputs.tsx (input.*, steps.*.formula.*,
    steps.*.result) y agrega: `values` (los números exactos o con 50 cifras,
    como texto), `result` (los cuatro resultados formateados), los LaTeX
    interpretados de x0/Δx y el modo angular. Las fórmulas de `steps` son
    LaTeX para KaTeX; `result` y `steps.*.result` son texto formateado con
    `decimals` decimales ("≈" si se redondea).
    """
    from sympy import latex

    r = propagar_error(
        latex_a_texto(function_latex, estricto=True),
        latex_a_texto(x0, estricto=True),
        latex_a_texto(delta_x, estricto=True),
        modo_angular=angle_mode,
        decimales=decimals,
    )
    v = r["valores"]

    def txt(clave):
        return texto_valor(v[clave], decimals)

    x0_tex = _tex_valor_exacto(r["x0"], v["x0"])
    dx_tex = _tex_valor_exacto(r["dx"], v["dx"])
    x1_tex = _tex_valor_exacto(r["x0_mas_dx"], v["x0_mas_dx"])
    grados = angle_mode == "deg"
    unidad = r"^{\circ}" if grados else ""
    nota = r"\quad (x\text{ en grados})" if grados else ""

    d0, aprox, real, err = (txt(c) for c in ("derivada_en_x0", "delta_y_aprox", "delta_y_real", "error_absoluto"))
    f0, f1 = txt("f_x0"), txt("f_x0_dx")
    rel_f = r"\approx" if f0.startswith("≈") or f1.startswith("≈") else "="

    # f'(x0) exacto sólo si es corto (π√3/360 sí; una expresión de 40 términos no).
    from sympy import count_ops
    exacto_d0 = ""
    if not v["derivada_en_x0"][1] and count_ops(r["derivada_en_x0"]) <= 12:
        exacto_d0 = f" = {latex(r['derivada_en_x0'])}"

    steps = {
        "derivative": {
            "operation": {"expression": r"f'(x) = \frac{d}{dx} f(x)"},
            "formula": {
                "function": f"f(x) = {r['funcion_latex']}{nota}",
                "derivative": f"f'(x) = {r['derivada_latex']}",
                "evaluation": (
                    f"f'({x0_tex}{unidad}){exacto_d0} {_relacion(d0)} {_tex_numero(d0)}"
                ),
            },
            "result": d0,
        },
        "approx_delta_y": {
            "operation": {"expression": r"\Delta y_{\text{aprox}} \approx f'(x_0)\,\Delta x"},
            "formula": {
                "expression": (
                    rf"\Delta y_{{\text{{aprox}}}} \approx f'(x_0)\,\Delta x"
                    rf" = {_entre_parentesis(_tex_numero(d0))} \cdot {_entre_parentesis(dx_tex)}"
                    rf" {_relacion(aprox)} {_tex_numero(aprox)}"
                ),
            },
            "result": aprox,
        },
        "exact_delta_y": {
            "operation": {"expression": r"\Delta y_{\text{real}} = f(x_0 + \Delta x) - f(x_0)"},
            "formula": {
                "expression": (
                    rf"\Delta y_{{\text{{real}}}} = f({x1_tex}{unidad}) - f({x0_tex}{unidad})"
                    rf" {rel_f} {_tex_numero(f1)} - {_entre_parentesis(_tex_numero(f0))}"
                    rf" {_relacion(real)} {_tex_numero(real)}"
                ),
            },
            "result": real,
        },
        "absolute_error": {
            "operation": {"expression": r"e_a = \left|\Delta y_{\text{real}} - \Delta y_{\text{aprox}}\right|"},
            "formula": {
                "numerator": (
                    rf"e_a = \left|{_tex_numero(real)} - {_entre_parentesis(_tex_numero(aprox))}\right|"
                    rf" {_relacion(err)} {_tex_numero(err)}"
                ),
            },
            "result": err,
        },
    }

    return {
        "input": {
            "function_latex": function_latex,
            "x0": txt("x0"),
            "delta_x": txt("dx"),
            "x0_latex": x0_tex,
            "delta_x_latex": dx_tex,
            "function_interpreted_latex": r["funcion_latex"],
            "angle_mode": angle_mode,
            "decimals": decimals,
        },
        "steps": steps,
        "result": {
            "derivative_at_x0": d0,
            "delta_y_approx": aprox,
            "delta_y_real": real,
            "absolute_error": err,
        },
        "values": {
            "x0": texto_preciso(v["x0"]),
            "delta_x": texto_preciso(v["dx"]),
            "f_x0": texto_preciso(v["f_x0"]),
            "f_x0_dx": texto_preciso(v["f_x0_dx"]),
            "derivative_at_x0": texto_preciso(v["derivada_en_x0"]),
            "delta_y_approx": texto_preciso(v["delta_y_aprox"]),
            "delta_y_real": texto_preciso(v["delta_y_real"]),
            "absolute_error": texto_preciso(v["error_absoluto"]),
        },
    }
