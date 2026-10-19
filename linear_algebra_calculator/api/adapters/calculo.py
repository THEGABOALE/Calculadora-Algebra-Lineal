"""
calculus/derivate y calculus/integral -- core/calculo.py.

Traduce el LaTeX con latex_a_texto (el mismo traductor que usan los métodos
numéricos) y deriva en core/. El sobre {"ok": true, "data": {...}} es el
que lee DerivativeInputs.tsx (`res.data.result.latex`); los errores siguen
el formato del resto de la API, {"error": {"code", "message"}}, y los arma
la vista.
"""

from __future__ import annotations

from typing import Any, Dict

from core import calculo
from core.calculo import derivar_simbolica

from .latex import latex_a_texto


def derivative(*, function_latex: str, variable: str = "x") -> Dict[str, Any]:
    texto = latex_a_texto(function_latex, estricto=True)
    r = derivar_simbolica(texto, variable)
    return {
        "ok": True,
        "data": {
            "input": {
                "latex": function_latex,
                "variable": r["variable"],
                # Lo que se entendió de la entrada, para que el usuario vea
                # si el teclado matemático produjo la función que quería.
                "expression": str(r["funcion"]),
                "interpreted_latex": r["funcion_latex"],
            },
            "result": {
                "latex": r["derivada_latex"],
                "expression": r["derivada_texto"],
            },
        },
    }


def integral(*, function_latex: str, variable: str = "x") -> Dict[str, Any]:
    """Integral indefinida, en un proceso aparte con límite de tiempo.

    Levanta ValueError (entrada), calculo.IntegralNoResuelta o
    calculo.CalculoDemasiadoCostoso; la vista los traduce a HTTP.
    """
    texto = latex_a_texto(function_latex, estricto=True)
    r = calculo.integrar_con_limite(texto, variable, segundos=calculo.TIEMPO_MAXIMO_INTEGRAL_S)
    return {
        "ok": True,
        "data": {
            "input": {
                "latex": function_latex,
                "variable": r["variable"],
                "interpreted_latex": r["funcion_latex"],
                "expression": r["funcion_texto"],
            },
            "result": {
                # Con la constante de integración; `expression` no la lleva,
                # para que la primitiva siga siendo verificable.
                "latex": r["primitiva_latex"],
                "expression": r["primitiva_texto"],
                "special_functions": r["funciones_especiales"],
                "definitions": r["definiciones"],
                "note": r["nota"],
            },
        },
    }


__all__ = ["derivative", "integral"]
