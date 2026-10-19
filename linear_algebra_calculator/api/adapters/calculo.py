"""
calculus/derivate -- core/calculo.py.

Traduce el LaTeX con latex_a_texto (el mismo traductor que usan los métodos
numéricos) y deriva en core/. El sobre {"ok": true, "data": {...}} es el
que lee DerivativeInputs.tsx (`res.data.result.latex`); los errores siguen
el formato del resto de la API, {"error": {"code", "message"}}, y los arma
la vista.
"""

from __future__ import annotations

from typing import Any, Dict

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


__all__ = ["derivative"]
