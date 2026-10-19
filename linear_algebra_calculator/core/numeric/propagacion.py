"""
PROPAGACIÓN DE ERROR (issue #11)

    f'(x0)                          derivada simbólica evaluada en x0
    Δy_aprox = f'(x0)·Δx            aproximación lineal (diferencial)
    Δy_real  = f(x0 + Δx) - f(x0)   incremento exacto de f
    e_a      = |Δy_real - Δy_aprox|  error de la aproximación lineal

MODO ANGULAR: una sola estrategia, transformar la función antes de derivar.
Con "deg", parsear() lee sin(x) como sin(πx/180) (lo mismo que hace la
Secante desde el issue #24): x0 y Δx se interpretan en grados y se evalúan
tal cual, sin convertirlos otra vez, y la derivada respecto de esa misma
coordenada sale con el factor π/180 por regla de la cadena:
d/dx sin(πx/180) = (π/180)·cos(πx/180). Las funciones sin trigonométricas
dan exactamente lo mismo en los dos modos.

Sólo sin, cos y tan tienen conversión a grados. En "deg" se RECHAZAN las
demás trigonométricas (sec, csc, cot) y las inversas (asin, ...): se
evaluarían en radianes y el resultado se presentaría como si fuera en
grados.

EXACTITUD: x0 y Δx se leen como números exactos de sympy (0.1 -> 1/10,
\\frac{\\pi}{4} -> π/4), f(x0), f(x0+Δx) y f'(x0) se construyen exactos y
recién al final se evalúan con PRECISION cifras significativas (evalf de
sympy, que sube la precisión interna cuando hay cancelación, como en
f(x0+Δx) - f(x0) con Δx chico). Los valores racionales con expresión
decimal finita se devuelven exactos (2.1² - 4 = 0.41). La presentación
(`decimales`) redondea con "≈" sólo al mostrar.

DOMINIO: f(x0), f(x0+Δx) y f'(x0) tienen que ser reales y finitos; si no
(1/x en 0, ln de un negativo, √ de un negativo, f' infinita en x0) se
rechaza con ValueError. Si la derivada contiene sign(g(x)) y g(x0) = 0 (|x|
en 0), f no es derivable en x0: sympy diría sign(0) = 0, que no es una
derivada.

LÍMITES: x0, Δx, f(x0), f(x0+Δx) y f'(x0) de magnitud ≤ 1e100, y
exponentes numéricos de f de valor absoluto ≤ 1000 (x^{10^9} en x0 = 2
construiría un entero de mil millones de bits).
"""

from __future__ import annotations

from decimal import Context, Decimal
from typing import Any, Dict, Tuple

from core.calculo import derivar_simbolica
from core.numeric._expresiones import parsear, validar_modo_angular
from core.numeric.errores import texto_compacto, texto_redondeado, validar_decimales

PRECISION = 50
MAGNITUD_MAXIMA = Decimal("1e100")
EXPONENTE_MAXIMO = 1000
LARGO_VALOR_MAXIMO = 100
_DECIMAL = Context(prec=PRECISION + 10)


def leer_valor(texto: str, nombre: str):
    """x0 o Δx: expresión numérica exacta (sin variables), real y finita."""
    from sympy import nsimplify

    if not isinstance(texto, str) or not texto.strip():
        raise ValueError(f"Ingresá {nombre}.")
    if len(texto) > LARGO_VALOR_MAXIMO:
        raise ValueError(f"{nombre} es demasiado largo (máximo {LARGO_VALOR_MAXIMO} caracteres).")
    try:
        expr, _ = parsear(texto)
    except ValueError:
        # El mensaje de parsear() habla de "la función f(x)": acá el campo es
        # un número, así que se reemplaza por uno que lo nombre.
        raise ValueError(
            f"{nombre} debe ser un valor numérico, sin variables "
            "(por ejemplo 30, 0.5, una fracción o π)."
        ) from None
    if expr.free_symbols:
        raise ValueError(f"{nombre} debe ser un valor numérico, sin variables.")
    valor = nsimplify(expr, rational=True)
    _exigir_real_finito(valor, nombre, f"{nombre} debe ser un número real y finito.")
    return valor


def _numero(valor):
    """evalf de un valor exacto, o None si no es un real finito."""
    try:
        aproximado = valor.evalf(PRECISION)
    except Exception:
        return None
    if aproximado.is_real is not True or aproximado.is_finite is not True:
        return None
    if not aproximado.is_number:
        return None
    return aproximado


def _exigir_real_finito(valor, nombre: str, mensaje: str):
    aproximado = _numero(valor)
    if aproximado is None:
        raise ValueError(mensaje)
    if abs(aproximado) > MAGNITUD_MAXIMA:
        raise ValueError(f"{nombre} supera 1e100 en valor absoluto.")
    return aproximado


def a_decimal(valor) -> Tuple[Decimal, bool]:
    """(Decimal, es_exacto). Exacto si es racional con expresión decimal finita."""
    from sympy import Rational

    if isinstance(valor, Rational):
        q = int(valor.q)
        while q % 2 == 0:
            q //= 2
        while q % 5 == 0:
            q //= 5
        if q == 1:
            return _DECIMAL.divide(Decimal(int(valor.p)), Decimal(int(valor.q))), True
    aproximado = valor.evalf(PRECISION)
    return Decimal(str(aproximado)), False


def _rechazar_trigonometricas_sin_grados(funcion) -> None:
    from sympy import cos, sin, tan
    from sympy.functions.elementary.trigonometric import (
        InverseTrigonometricFunction,
        TrigonometricFunction,
    )

    ajenas = sorted({type(t).__name__ for t in funcion.atoms(TrigonometricFunction)
                     if t.func not in (sin, cos, tan)}
                    | {type(t).__name__ for t in funcion.atoms(InverseTrigonometricFunction)})
    if ajenas:
        raise ValueError(
            f"En grados sólo se admiten sin, cos y tan; {', '.join(ajenas)} se evaluaría "
            "en radianes. Usá el modo radianes o reescribí la función con sin, cos y tan."
        )


def _rechazar_exponentes_enormes(funcion) -> None:
    from sympy import Pow

    for potencia in funcion.atoms(Pow):
        exponente = potencia.exp
        if exponente.is_number and abs(exponente.evalf(15)) > EXPONENTE_MAXIMO:
            raise ValueError(f"La función tiene un exponente mayor que {EXPONENTE_MAXIMO} en valor absoluto.")


def _no_derivable_en(derivada, x, x0) -> bool:
    from sympy import sign

    for s in derivada.atoms(sign):
        if s.args[0].subs(x, x0).evalf(PRECISION) == 0:
            return True
    return False


def propagar_error(
    f_str: str,
    x0_str: str,
    dx_str: str,
    modo_angular: str = "rad",
    decimales: int = 6,
) -> Dict[str, Any]:
    """Propagación de error de f en x0 con incremento Δx (textos planos).

    Devuelve expresiones exactas de sympy ("funcion", "derivada", "x0",
    "dx", "f_x0", "f_x0_dx", "derivada_en_x0", "delta_y_aprox",
    "delta_y_real", "error_absoluto") y sus valores en Decimal en "valores"
    como pares (Decimal, es_exacto). Levanta ValueError si alguna entrada no
    es válida o cae fuera del dominio.
    """
    from sympy import Abs

    validar_modo_angular(modo_angular)
    validar_decimales(decimales)
    x0 = leer_valor(x0_str, "x₀")
    dx = leer_valor(dx_str, "Δx")

    d = derivar_simbolica(f_str, "x", modo_angular)
    funcion, derivada = d["funcion"], d["derivada"]
    (x,) = funcion.free_symbols or derivada.free_symbols or {None}
    if x is None:  # función constante: cualquier símbolo sirve para sustituir
        from sympy import Symbol
        x = Symbol("x", real=True)
    if modo_angular == "deg":
        _rechazar_trigonometricas_sin_grados(funcion)
    _rechazar_exponentes_enormes(funcion)

    f_x0 = funcion.subs(x, x0)
    f_x0_dx = funcion.subs(x, x0 + dx)
    for valor, donde in ((f_x0, "x₀"), (f_x0_dx, "x₀ + Δx")):
        _exigir_real_finito(
            valor, f"f({donde})",
            f"f no está definida (como número real) en {donde}: el punto está fuera del dominio de la función.",
        )

    derivada_en_x0 = derivada.subs(x, x0)
    if _no_derivable_en(derivada, x, x0):
        raise ValueError("f no es derivable en x₀ (la derivada cambia de valor a cada lado del punto).")
    _exigir_real_finito(derivada_en_x0, "f'(x₀)", "f no es derivable en x₀: f'(x₀) no está definida.")

    delta_y_aprox = derivada_en_x0 * dx
    delta_y_real = f_x0_dx - f_x0
    error_absoluto = Abs(delta_y_real - delta_y_aprox)

    exactos = {
        "x0": x0, "dx": dx, "x0_mas_dx": x0 + dx, "f_x0": f_x0, "f_x0_dx": f_x0_dx,
        "derivada_en_x0": derivada_en_x0, "delta_y_aprox": delta_y_aprox,
        "delta_y_real": delta_y_real, "error_absoluto": error_absoluto,
    }
    valores = {clave: a_decimal(v) for clave, v in exactos.items()}
    return {
        "modo_angular": modo_angular,
        "decimales": decimales,
        "funcion": funcion,
        "funcion_latex": d["funcion_latex"],
        "derivada": derivada,
        "derivada_latex": d["derivada_latex"],
        "simbolo": x,
        **exactos,
        "valores": valores,
    }


def texto_valor(par: Tuple[Decimal, bool], decimales: int) -> str:
    """Presentación con `decimales` decimales ("≈" si se redondea)."""
    valor, exacto = par
    texto = texto_redondeado(valor, decimales)
    if not exacto and not texto.startswith("≈"):
        # El Decimal de evalf no es el valor exacto (irracional): aunque el
        # redondeo coincida con él, lo mostrado es una aproximación.
        texto = f"≈ {texto}"
    return texto


def texto_preciso(par: Tuple[Decimal, bool]) -> str:
    """Valor exacto, o con PRECISION cifras si es irracional."""
    return texto_compacto(par[0])


__all__ = ["PRECISION", "leer_valor", "propagar_error", "texto_preciso", "texto_valor"]
