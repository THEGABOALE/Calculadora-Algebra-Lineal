"""
CÁLCULO SIMBÓLICO: derivadas (issue #10).

    derivar_simbolica("x**2*sin(x)")  ->  x**2*cos(x) + 2*x*sin(x)

Recibe la función como texto plano (el mismo formato que core/numeric: la
API traduce antes el LaTeX con api/adapters/latex.py) y la deriva con
sympy.diff, exacta.

Por qué no reutilizar core.numeric._expresiones.derivar(): esa función
rechaza una derivada idénticamente nula porque Newton-Raphson divide por
f'(x) y con f' = 0 su fórmula no está definida. Esa regla es del MÉTODO, no
de la derivada: d/dx(7) = 0 es un resultado correcto acá. Se reutiliza, en
cambio, parsear(): las mismas funciones admitidas, la misma traducción de
"^" a potencia y "e" a la constante de Euler, y el mismo rechazo de
funciones desconocidas y de letras que no son la variable.

DECISIONES
- Variable elegible: una letra minúscula ASCII que no sea "e" (reservada
  para la constante de Euler). La expresión sólo puede usar esa letra; no
  hay parámetros simbólicos (a, b, ...): d/dx(a·x) no es una derivada de
  una variable sino una parcial con constantes, fuera de alcance.
- La variable es REAL: con el símbolo complejo por defecto de sympy,
  d|x|/dx sale en términos de re(x) e im(x); con una variable real es sign(x).
- Los decimales se convierten a racionales exactos (0.5 -> 1/2) antes de
  derivar, para que el resultado sea simbólico y no "1.0*x".
- Simplificación: sympy.simplify a veces acorta (d/dx((x+1)/(x-1)) ->
  -2/(x-1)^2) y a veces sólo reordena o factoriza (x^2 cos x + 2x sin x ->
  x(x cos x + 2 sin x)). Se usa la forma simplificada sólo si reduce las
  operaciones al menos un 25 %; si no, queda la forma de sympy.diff, que es
  la de la regla aplicada.
- Operadores de cálculo dentro de la entrada (∫, d/dx, sumatorias, límites)
  se rechazan: la entrada es la función a derivar, no otra operación.

sympy se importa dentro de las funciones, nunca a nivel de módulo (misma
regla que core/numeric/_expresiones.py: el CLI no paga sympy al arrancar).
"""

from __future__ import annotations

import re
from typing import Any, Dict

from core.numeric._expresiones import parsear

_VARIABLE = re.compile(r"[a-df-z]")
LARGO_MAXIMO = 500
_UMBRAL_SIMPLIFICACION = 0.75
_OPERACIONES_MAXIMAS_PARA_SIMPLIFICAR = 200


def validar_variable(variable: str) -> None:
    if not isinstance(variable, str) or not _VARIABLE.fullmatch(variable):
        raise ValueError(
            "La variable de derivación debe ser una sola letra minúscula "
            "(por ejemplo x o t), distinta de e, que es la constante de Euler."
        )


def _rechazar_operadores_de_calculo(expr) -> None:
    from sympy import Derivative, Integral, Limit, Product, Sum

    nombres = {Derivative: "una derivada", Integral: "una integral", Sum: "una sumatoria",
               Product: "un producto", Limit: "un límite"}
    for tipo, nombre in nombres.items():
        if expr.has(tipo):
            raise ValueError(
                f"La expresión contiene {nombre}: escribí sólo la función a derivar."
            )


def _simplificar(derivada):
    from sympy import count_ops, simplify

    operaciones = count_ops(derivada)
    if operaciones == 0 or operaciones > _OPERACIONES_MAXIMAS_PARA_SIMPLIFICAR:
        return derivada
    simplificada = simplify(derivada)
    if count_ops(simplificada) <= _UMBRAL_SIMPLIFICACION * operaciones:
        return simplificada
    return derivada


def derivar_simbolica(f_str: str, variable: str = "x") -> Dict[str, Any]:
    """Derivada exacta de f respecto de `variable`.

    Devuelve {"variable", "funcion", "funcion_latex", "derivada",
    "derivada_latex", "derivada_texto"}: `funcion` y `derivada` son
    expresiones de sympy; los *_latex, LaTeX de sympy (renderizable por
    MathQuill/KaTeX); `derivada_texto`, el str() de sympy.

    Levanta ValueError (con un mensaje para el usuario) si la variable no es
    válida, el texto no se puede interpretar, usa funciones desconocidas o
    letras distintas de la variable, o contiene operadores de cálculo.
    """
    from sympy import Symbol, diff, latex, nsimplify

    validar_variable(variable)
    if not isinstance(f_str, str) or not f_str.strip():
        raise ValueError("Ingresá la función a derivar.")
    if len(f_str) > LARGO_MAXIMO:
        raise ValueError(f"La expresión es demasiado larga (máximo {LARGO_MAXIMO} caracteres).")

    expr, simbolo = parsear(f_str, variable=variable)
    _rechazar_operadores_de_calculo(expr)

    real = Symbol(variable, real=True)
    expr = nsimplify(expr.subs(simbolo, real), rational=True)
    derivada = _simplificar(diff(expr, real))

    return {
        "variable": variable,
        "funcion": expr,
        "funcion_latex": latex(expr),
        "derivada": derivada,
        "derivada_latex": latex(derivada),
        "derivada_texto": str(derivada),
    }


__all__ = ["LARGO_MAXIMO", "derivar_simbolica", "validar_variable"]
