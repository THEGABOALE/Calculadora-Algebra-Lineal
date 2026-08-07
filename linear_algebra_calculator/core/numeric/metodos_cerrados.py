"""
MÉTODOS CERRADOS DE BÚSQUEDA DE RAÍCES
- Bisección
- Regla Falsa (False Position)

Ambos métodos requieren un intervalo [a,b] donde f(a)·f(b) < 0.

La evaluación de f(x) ya no usa eval(): vive en `_expresiones`, que parsea con
sympy. La nota de seguridad que traía este archivo sobre el safe_dict del
eval() dejó de aplicar.

VALIDACIÓN: el chequeo de Bolzano (f(a)·f(b) < 0) vive acá, en el motor, no en
la capa que llama. En el repo del que se porta la estructura de salida, esa
validación estaba en BisectionSerializer.validate -- es decir, en la capa
HTTP -- así que el algoritmo aceptaba intervalos sin cambio de signo y
devolvía una raíz falsa a cualquier consumidor que no fuera la API REST. Acá
CLI y web heredan el mismo rechazo sin duplicarlo.

CRITERIO DE PARO: los dos motores cortaban distinto y no son intercambiables.
El original corta cuando el error relativo porcentual entre aproximaciones
sucesivas baja de la tolerancia; el portado corta cuando la longitud del
intervalo baja de la tolerancia. Se soportan ambos vía `criterio`, con el
original por default para no cambiar el significado de `tolerancia` en las
llamadas que ya existían.
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from core.numeric._expresiones import (
    a_latex,
    compilar,
    error_relativo as calcular_error_relativo,
    evaluar,
)

CRITERIOS = ("error_relativo", "intervalo")


def verificar_intervalo(f_str: str, a: float, b: float) -> bool:
    """
    Verifica que f(a) · f(b) < 0 (cambio de signo en el intervalo).
    """
    try:
        f, _, _ = compilar(f_str)
        fa = evaluar(f, a, f_str)
        fb = evaluar(f, b, f_str)
        return fa * fb < 0
    except Exception:
        return False


def _validar(f_str: str, a: float, b: float, tolerancia: float, criterio: str) -> None:
    """Precondiciones comunes a bisección y regla falsa."""
    if criterio not in CRITERIOS:
        raise ValueError(f"Criterio desconocido: {criterio!r}. Usá uno de {CRITERIOS}.")
    if a >= b:
        raise ValueError(f"El intervalo no es válido: se requiere a < b (a={a}, b={b}).")
    if tolerancia <= 0:
        raise ValueError(f"La tolerancia debe ser positiva (tolerancia={tolerancia}).")
    if not verificar_intervalo(f_str, a, b):
        raise ValueError("El intervalo no es válido: f(a)·f(b) debe ser < 0")


def _estimacion_iteraciones(a: float, b: float, tolerancia: float) -> Dict[str, Any]:
    """Cota de iteraciones n >= log2((b-a)/E), sólo con criterio='intervalo'."""
    longitud = b - a
    estimado = math.log2(longitud / tolerancia)
    return {
        "longitud_intervalo": longitud,
        "tolerancia": tolerancia,
        "estimado": estimado,
        "n_minimo": max(1, math.ceil(estimado)),
        "latex": {
            "formula": r"n \ge \log_{2}\!\left(\frac{b-a}{E}\right)",
            "sustitucion": rf"n \ge \log_2\left(\frac{{{longitud:.4f}}}{{{tolerancia:.4g}}}\right)",
            "numerico": rf"n \ge {estimado:.4f}",
        },
    }


def _corta(criterio: str, error_actual: float, longitud: float, tolerancia: float, i: int) -> bool:
    if criterio == "intervalo":
        return longitud < tolerancia
    return error_actual < tolerancia and i > 1


def _resultado(
    metodo: str,
    xr: float,
    i: int,
    historial: List[Dict],
    error_actual: float,
    a: float,
    b: float,
    detalles: List[Dict],
    expr,
    criterio: str,
    tolerancia: float,
    estimacion: Optional[Dict[str, Any]],
    advertencia: Optional[str] = None,
) -> Dict:
    resultado = {
        "raiz": xr,
        "iteraciones": i,
        "historial": historial,
        "error_final": error_actual,
        "intervalo_final": (a, b),
        "metodo": metodo,
        "criterio": criterio,
        "funcion_latex": a_latex(expr),
        "detalles": detalles,
        "conclusion": {
            "raiz": xr,
            "iteraciones": i,
            "criterio_paro": (
                "longitud_intervalo < tolerancia"
                if criterio == "intervalo"
                else "error_relativo < tolerancia"
            ),
            "latex": (
                rf"\text{{{metodo} converge en }} {i} \text{{ iteraciones. }}"
                rf"\text{{La raíz aproximada es }} x_r = {xr:.6f}."
            ),
        },
    }
    if estimacion is not None:
        resultado["estimacion_iteraciones"] = estimacion
    if advertencia is not None:
        resultado["advertencia"] = advertencia
    return resultado


def _detalle_iteracion(i: int, a: float, b: float, xr: float, fxr: float, error: float) -> Dict:
    lineas = [
        rf"x_r = \frac{{a + b}}{{2}} = \frac{{{a:.6f} + {b:.6f}}}{{2}} = {xr:.6f}",
        rf"f(x_r) = {fxr:.6e}",
    ]
    if error != float("inf"):
        lineas.append(rf"E_a = {error:.6f}\%")
    return {"iteracion": i, "lineas": lineas}


def metodo_biseccion(
    f_str: str,
    a: float,
    b: float,
    tolerancia: float,
    criterio: str = "error_relativo",
    max_iter: int = 100,
) -> Dict:
    """
    Método de Bisección para encontrar raíces.

    Parámetros:
    - f_str: función como string (ej: "x**2 - 4")
    - a: límite inferior del intervalo
    - b: límite superior del intervalo
    - tolerancia: umbral de corte; su significado depende de `criterio`
    - criterio: "error_relativo" (error relativo porcentual entre iteraciones)
      o "intervalo" (longitud del intervalo)
    - max_iter: máximo número de iteraciones

    Retorna:
    - Dict con: raiz, iteraciones, historial, error_final, intervalo_final,
      metodo, criterio, funcion_latex, detalles, conclusion, y además
      estimacion_iteraciones con criterio="intervalo" y advertencia si no
      convergió.
    """
    _validar(f_str, a, b, tolerancia, criterio)
    f, expr, _ = compilar(f_str)

    estimacion = _estimacion_iteraciones(a, b, tolerancia) if criterio == "intervalo" else None

    historial: List[Dict] = []
    detalles: List[Dict] = []
    xr_anterior = a
    error_actual = float("inf")
    xr = a

    for i in range(1, max_iter + 1):
        xr = (a + b) / 2.0
        fxr = evaluar(f, xr, f_str)
        fa = evaluar(f, a, f_str)
        fb = evaluar(f, b, f_str)

        error_actual = calcular_error_relativo(xr, xr_anterior) if i > 1 else float("inf")
        longitud = b - a

        historial.append(
            {
                "iteracion": i, "a": a, "b": b, "xr": xr,
                "f(a)": fa, "f(b)": fb, "f(xr)": fxr,
                "error": error_actual,
            }
        )
        detalles.append(_detalle_iteracion(i, a, b, xr, fxr, error_actual))

        if _corta(criterio, error_actual, longitud, tolerancia, i):
            return _resultado(
                "Bisección", xr, i, historial, error_actual, a, b, detalles,
                expr, criterio, tolerancia, estimacion,
            )

        if fa * fxr < 0:
            b = xr
        else:
            a = xr

        xr_anterior = xr

    return _resultado(
        "Bisección", xr, max_iter, historial, error_actual, a, b, detalles,
        expr, criterio, tolerancia, estimacion,
        advertencia="Alcanzado número máximo de iteraciones",
    )


def metodo_regla_falsa(
    f_str: str,
    a: float,
    b: float,
    tolerancia: float,
    criterio: str = "error_relativo",
    max_iter: int = 100,
) -> Dict:
    """
    Método de Regla Falsa (False Position) para encontrar raíces.

    Misma firma y mismo contrato de salida que `metodo_biseccion`.
    """
    _validar(f_str, a, b, tolerancia, criterio)
    f, expr, _ = compilar(f_str)

    estimacion = _estimacion_iteraciones(a, b, tolerancia) if criterio == "intervalo" else None

    historial: List[Dict] = []
    detalles: List[Dict] = []
    xr_anterior = a
    error_actual = float("inf")
    xr = a

    for i in range(1, max_iter + 1):
        fa = evaluar(f, a, f_str)
        fb = evaluar(f, b, f_str)

        denominador = fb - fa
        if denominador == 0:
            raise ZeroDivisionError(
                f"En la iteración {i} se obtuvo f(b) - f(a) = 0: la recta secante es "
                "horizontal y la regla falsa no puede continuar."
            )

        xr = b - (fb * (b - a)) / denominador
        fxr = evaluar(f, xr, f_str)

        error_actual = calcular_error_relativo(xr, xr_anterior) if i > 1 else float("inf")
        longitud = b - a

        historial.append(
            {"iteracion": i, "a": a, "b": b, "xr": xr, "f(xr)": fxr, "error": error_actual}
        )
        detalles.append(
            {
                "iteracion": i,
                "lineas": [
                    rf"x_r = b - \frac{{f(b)\,(b-a)}}{{f(b)-f(a)}} = {xr:.6f}",
                    rf"f(x_r) = {fxr:.6e}",
                ]
                + ([rf"E_a = {error_actual:.6f}\%"] if error_actual != float("inf") else []),
            }
        )

        if _corta(criterio, error_actual, longitud, tolerancia, i):
            return _resultado(
                "Regla Falsa", xr, i, historial, error_actual, a, b, detalles,
                expr, criterio, tolerancia, estimacion,
            )

        if fa * fxr < 0:
            b = xr
        else:
            a = xr

        xr_anterior = xr

    return _resultado(
        "Regla Falsa", xr, max_iter, historial, error_actual, a, b, detalles,
        expr, criterio, tolerancia, estimacion,
        advertencia="Alcanzado número máximo de iteraciones",
    )


__all__ = [
    "CRITERIOS",
    "verificar_intervalo",
    "metodo_biseccion",
    "metodo_regla_falsa",
]
