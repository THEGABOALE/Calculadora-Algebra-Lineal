"""
Parseo y evaluación de funciones f(x) escritas como texto.

Reemplaza las dos copias de `evaluar_funcion` que vivían duplicadas en
metodos_cerrados.py y metodos_abiertos.py (cuerpo identico, sólo cambiaban
comentarios y el texto de una excepcion). Las dos usaban `eval()` sobre el
string con un dict restringido; aca se usa sympy, que ademas da derivada
simbolica exacta para Newton-Raphson.

IMPORTANTE -- sympy se importa DENTRO de las funciones, nunca a nivel de
modulo. `cli/startup.py` importa `cli.numerical_methods_runners` a nivel de
modulo, y ese runner importa `core.numeric.*` tambien a nivel de modulo: si
sympy se cargara arriba, el CLI entero lo pagaria en cada arranque, antes de
mostrar el menu, aunque el usuario sólo vaya a resolver una matriz. Es el mismo
problema que documenta utils/symbolic_equations.py para symengine, que se
cargaba en cada arranque de la web por venir arrastrado desde
utils.EquationFunctions.

`tests/test_metodos_numericos.py` fija esta regla: verifica que 'sympy' no
quede en sys.modules tras importar cli.startup ni calculator.views.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

# Nombres que el usuario puede escribir en f(x). Es el mismo repertorio que
# aceptaba el safe_dict del eval() anterior, para no romper entradas validas.
FUNCIONES_SOPORTADAS: Tuple[str, ...] = (
    "sin", "cos", "tan", "exp", "log", "log10", "sqrt", "abs", "pi", "e",
)


def normalizar(f_str: str) -> str:
    """Traduce la notacion del usuario a la que entiende sympy.

    `^` significa potencia para quien escribe la funcion, pero en sympy (como
    en Python) es XOR binario: `x^2` se parsearia como `Xor(x, 2)` en vez de
    `x**2`, sin error y con un resultado silenciosamente incorrecto. El eval()
    anterior hacia este mismo reemplazo y hay que conservarlo.
    """
    return f_str.replace("^", "**")


def _diccionario_local() -> Dict[str, Any]:
    """Mapea los nombres soportados a sus equivalentes de sympy."""
    from sympy import Abs, E, cos, exp, log, pi, sin, sqrt, tan

    return {
        "sin": sin,
        "cos": cos,
        "tan": tan,
        "exp": exp,
        "log": log,
        "log10": lambda arg: log(arg, 10),
        "sqrt": sqrt,
        "abs": Abs,
        "Abs": Abs,
        "pi": pi,
        "e": E,
        "E": E,
    }


def parsear(f_str: str):
    """Devuelve `(expr, x)` a partir del texto de la funcion.

    Levanta ValueError si el texto no parsea o si usa una variable distinta de
    x. La validacion vive aca, en el motor, y no en la capa que llama: CLI y
    web heredan el mismo rechazo sin duplicarlo.
    """
    from sympy import Symbol
    from sympy.parsing.sympy_parser import parse_expr

    x = Symbol("x")
    texto = normalizar(f_str)

    try:
        expr = parse_expr(texto, local_dict=_diccionario_local(), evaluate=True)
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar la funcion f(x) = {f_str}: {exc}") from exc

    libres = {s.name for s in expr.free_symbols}
    if libres - {"x"}:
        ajenas = ", ".join(sorted(libres - {"x"}))
        raise ValueError(
            f"La funcion f(x) = {f_str} usa variables no soportadas: {ajenas}. "
            "La unica variable permitida es x."
        )

    # sympy no falla ante un nombre de funcion desconocido: `sen(x)` parsea
    # como una funcion indefinida y su nombre no aparece en free_symbols, asi
    # que el chequeo de variables de arriba lo deja pasar. Sin esto, un typo
    # muy probable en castellano (sen por sin) llegaria hasta lambdify y
    # reventaria recien al evaluar, con un mensaje que no dice que el nombre
    # esta mal. El eval() anterior lo cortaba de una con NameError.
    from sympy.core.function import AppliedUndef

    indefinidas = sorted({type(fn).__name__ for fn in expr.atoms(AppliedUndef)})
    if indefinidas:
        nombres = ", ".join(indefinidas)
        soportadas = ", ".join(FUNCIONES_SOPORTADAS)
        raise ValueError(
            f"La funcion f(x) = {f_str} usa funciones desconocidas: {nombres}. "
            f"Las soportadas son: {soportadas}."
        )

    return expr, x


def compilar(f_str: str) -> Tuple[Callable[[float], float], Any, Any]:
    """Devuelve `(f, expr, x)` donde `f` evalua numericamente f(x)."""
    from sympy import lambdify

    expr, x = parsear(f_str)
    return lambdify(x, expr, "math"), expr, x


def derivar(expr, x, derivada_str: str | None = None):
    """Derivada simbolica de `expr`, o la que provea `derivada_str`.

    Reemplaza a `calcular_derivada_numerica` (diferencias centrales, h=1e-8):
    la simbolica es exacta y no arrastra error de truncamiento. Se conserva la
    posibilidad de forzar una derivada escrita a mano porque el CLI la ofrecia.
    """
    from sympy import lambdify

    if derivada_str is not None:
        dexpr, _ = parsear(derivada_str)
    else:
        from sympy import diff

        dexpr = diff(expr, x)

    if dexpr == 0:
        raise ValueError(
            "La derivada de la funcion es cero: Newton-Raphson no es aplicable "
            "a una funcion constante."
        )

    return lambdify(x, dexpr, "math"), dexpr


def evaluar(f: Callable[[float], float], x_val: float, f_str: str = "") -> float:
    """Evalua f en x_val traduciendo cualquier fallo a ValueError."""
    try:
        return float(f(x_val))
    except Exception as exc:
        etiqueta = f" f(x) = {f_str}" if f_str else ""
        raise ValueError(f"Error al evaluar{etiqueta} en x = {x_val}: {exc}") from exc


def error_relativo(x_nuevo: float, x_viejo: float) -> float:
    """Error relativo porcentual entre dos aproximaciones sucesivas.

    Estaba duplicada identica en metodos_cerrados.py y metodos_abiertos.py.
    """
    if abs(x_nuevo) < 1e-15:  # Evitar division por cero
        return 0.0
    return abs((x_nuevo - x_viejo) / x_nuevo) * 100


def a_latex(expr) -> str:
    """Representacion LaTeX de una expresion, para el render web."""
    from sympy import latex

    return latex(expr)


__all__ = [
    "FUNCIONES_SOPORTADAS",
    "normalizar",
    "parsear",
    "compilar",
    "derivar",
    "evaluar",
    "error_relativo",
    "a_latex",
]
