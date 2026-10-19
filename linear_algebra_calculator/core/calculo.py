"""
CÁLCULO SIMBÓLICO: derivadas (issue #10) e integrales indefinidas (issue #12).

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
import threading
from typing import Any, Dict, List

from core.numeric._expresiones import parsear

_VARIABLE = re.compile(r"[a-df-z]")
LARGO_MAXIMO = 500
_UMBRAL_SIMPLIFICACION = 0.75
_OPERACIONES_MAXIMAS_PARA_SIMPLIFICAR = 200


def validar_variable(variable: str, operacion: str = "derivación") -> None:
    if not isinstance(variable, str) or not _VARIABLE.fullmatch(variable):
        raise ValueError(
            f"La variable de {operacion} debe ser una sola letra minúscula "
            "(por ejemplo x o t), distinta de e, que es la constante de Euler."
        )


def _rechazar_operadores_de_calculo(expr, accion: str = "derivar") -> None:
    from sympy import Derivative, Integral, Limit, Product, Sum

    nombres = {Derivative: "una derivada", Integral: "una integral", Sum: "una sumatoria",
               Product: "un producto", Limit: "un límite"}
    for tipo, nombre in nombres.items():
        if expr.has(tipo):
            raise ValueError(
                f"La expresión contiene {nombre}: escribí sólo la función a {accion}."
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


def derivar_simbolica(f_str: str, variable: str = "x", modo_angular: str = "rad") -> Dict[str, Any]:
    """Derivada exacta de f respecto de `variable`.

    Devuelve {"variable", "funcion", "funcion_latex", "derivada",
    "derivada_latex", "derivada_texto"}: `funcion` y `derivada` son
    expresiones de sympy; los *_latex, LaTeX de sympy (renderizable por
    MathQuill/KaTeX); `derivada_texto`, el str() de sympy.

    `modo_angular` se pasa a parsear(): con "deg", sin/cos/tan se leen en
    grados (sin(x) -> sin(πx/180)) ANTES de derivar, así que la derivada ya
    trae el factor π/180 de la regla de la cadena. calculus/derivate usa
    siempre el default "rad"; la propagación de error (core/numeric/
    propagacion.py) es la que pasa "deg".

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

    expr, simbolo = parsear(f_str, modo_angular=modo_angular, variable=variable)
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


# ---------------------------------------------------------------------------
# Integrales indefinidas (issue #12)
#
#     ∫ f(x) dx = F(x) + C,   F'(x) = f(x)
#
# POLÍTICA DE RESULTADOS
# - Primitiva con funciones elementales: se devuelve.
# - Primitiva con funciones especiales de una lista cerrada (erf, Si, Ei,
#   li, Fresnel, ...): se devuelve, con la lista de funciones especiales y
#   una nota que las define. Es una primitiva correcta (se verifica F' = f),
#   pero no elemental.
# - sympy devuelve la integral sin evaluar, una primitiva por tramos
#   (Piecewise) u otras funciones especiales: IntegralNoResuelta. El mensaje
#   dice que sympy NO ENCONTRÓ una primitiva admitida; nunca que no exista.
# - La constante de integración se agrega sólo al LaTeX ("F(x) + C"), nunca
#   a la expresión de sympy, que queda verificable.
# - Dominio real: la variable es real. Un ln(u) de la primitiva pasa a
#   ln|u| salvo que u sea positivo o que el integrando ya tenga ln(u) (que
#   restringe el dominio a u > 0): ∫1/x = ln|x| (válida en x < 0 y x > 0,
#   por separado), ∫tan x = -ln|cos x|, pero ∫ln x = x ln x - x. ln|u| y
#   ln u tienen la misma derivada u'/u donde están definidas.
#
# TIEMPO: sympy.integrate no tiene límite propio y algunos integrandos
# razonables no terminan (1/(x^5 + x + 1) supera los 30 s). integrar_con_
# limite corre el cálculo en un PROCESO aparte (multiprocessing "spawn",
# igual en Windows y Linux) y lo mata si se pasa del plazo: un hilo no se
# puede cancelar y seguiría consumiendo CPU después de responder. Un
# semáforo limita cuántos procesos de integración corren a la vez.
# ---------------------------------------------------------------------------

# Presupuesto total de un cálculo, arranque del proceso incluido (~1.5 s en
# Windows por importar sympy): por debajo de los 15 s de timeout del
# frontend (axios), con margen para la red y el render.
TIEMPO_MAXIMO_INTEGRAL_S = 10.0
OPERACIONES_MAXIMAS_INTEGRANDO = 60
INTEGRALES_SIMULTANEAS = 2
_ESPERA_TURNO_S = 1.0
_EN_CURSO = threading.BoundedSemaphore(INTEGRALES_SIMULTANEAS)

# Funciones especiales admitidas en una primitiva, con su definición (LaTeX
# que MathQuill 0.10 renderiza: sin espaciados como "\,", que no soporta).
FUNCIONES_ESPECIALES = {
    "erf": r"\operatorname{erf}(x) = \frac{2}{\sqrt{\pi}}\int_0^x e^{-t^2} dt",
    "erfi": r"\operatorname{erfi}(x) = \frac{2}{\sqrt{\pi}}\int_0^x e^{t^2} dt",
    "erfc": r"\operatorname{erfc}(x) = 1 - \operatorname{erf}(x)",
    "Si": r"\operatorname{Si}(x) = \int_0^x \frac{\sin t}{t} dt",
    "Ci": r"\operatorname{Ci}(x) = -\int_x^\infty \frac{\cos t}{t} dt",
    "Shi": r"\operatorname{Shi}(x) = \int_0^x \frac{\sinh t}{t} dt",
    "Chi": r"\operatorname{Chi}(x) = \gamma + \ln x + \int_0^x \frac{\cosh t - 1}{t} dt",
    "Ei": r"\operatorname{Ei}(x) = -\int_{-x}^\infty \frac{e^{-t}}{t} dt",
    "li": r"\operatorname{li}(x) = \int_0^x \frac{dt}{\ln t}",
    "fresnels": r"S(x) = \int_0^x \sin\left(\frac{\pi t^2}{2}\right)dt",
    "fresnelc": r"C(x) = \int_0^x \cos\left(\frac{\pi t^2}{2}\right)dt",
}


class IntegralNoResuelta(Exception):
    """sympy no encontró una primitiva presentable (ver la política arriba)."""


class CalculoDemasiadoCostoso(Exception):
    """El cálculo superó el presupuesto de tiempo."""


class ServidorOcupado(CalculoDemasiadoCostoso):
    """Ya hay INTEGRALES_SIMULTANEAS cálculos en curso (transitorio)."""


def _funciones_admitidas():
    from sympy import (
        Abs, Chi, Ci, Ei, Shi, Si, acos, acosh, acot, acoth, acsc, acsch, asec,
        asech, asin, asinh, atan, atanh, cos, cosh, cot, coth, csc, csch, erf,
        erfc, erfi, exp, fresnelc, fresnels, li, log, sec, sech, sign, sin, sinh,
        tan, tanh,
    )

    elementales = {exp, log, sin, cos, tan, cot, sec, csc, asin, acos, atan, acot,
                   asec, acsc, sinh, cosh, tanh, coth, sech, csch, asinh, acosh,
                   atanh, acoth, asech, acsch, Abs, sign}
    especiales = {erf, erfi, erfc, Si, Ci, Shi, Chi, Ei, li, fresnels, fresnelc}
    return elementales, especiales


def _con_valor_absoluto(F, f):
    """ln(u) -> ln|u| salvo u > 0 o ln(u) ya presente en el integrando."""
    from sympy import Abs, log

    en_integrando = {l.args[0] for l in f.atoms(log)}
    cambios = {}
    for l in F.atoms(log):
        u = l.args[0]
        if u.is_positive or u in en_integrando or isinstance(u, Abs):
            continue
        cambios[l] = log(Abs(u))
    return F.xreplace(cambios) if cambios else F


def _verificar_primitiva(F, f, x) -> None:
    """F' = f en puntos reales donde f está definida (defensa: no debería fallar)."""
    from sympy import Rational, diff

    dF = diff(F, x)
    for n in (-23, -13, -6, -2, 3, 5, 11, 19, 30):
        p = Rational(n, 7)
        fv = f.subs(x, p).evalf(30)
        if not (fv.is_real and fv.is_finite):
            continue
        dv = dF.subs(x, p).evalf(30)
        if not (dv.is_real and dv.is_finite) or abs(dv - fv) > 1e-15 * max(1, abs(fv)):
            raise IntegralNoResuelta(
                "sympy devolvió una expresión que no pasa la verificación F' = f; "
                "no se presenta como resultado."
            )


def preparar_integrando(f_str: str, variable: str = "x"):
    """Valida y parsea el integrando; devuelve (f, x) con x real.

    Barato: se corre en el proceso de la request antes de lanzar el cálculo,
    para responder los errores de entrada sin pagar el arranque del proceso.
    """
    from sympy import Symbol, count_ops, nsimplify

    validar_variable(variable, "integración")
    if not isinstance(f_str, str) or not f_str.strip():
        raise ValueError("Ingresá la función a integrar.")
    if len(f_str) > LARGO_MAXIMO:
        raise ValueError(f"La expresión es demasiado larga (máximo {LARGO_MAXIMO} caracteres).")
    expr, simbolo = parsear(f_str, variable=variable)
    _rechazar_operadores_de_calculo(expr, "integrar")
    if count_ops(expr) > OPERACIONES_MAXIMAS_INTEGRANDO:
        raise ValueError(
            f"La expresión es demasiado compleja para integrarla "
            f"(más de {OPERACIONES_MAXIMAS_INTEGRANDO} operaciones)."
        )
    x = Symbol(variable, real=True)
    return nsimplify(expr.subs(simbolo, x), rational=True), x


def integrar_simbolica(f_str: str, variable: str = "x") -> Dict[str, Any]:
    """∫ f d(variable), sin límite de tiempo (ver integrar_con_limite).

    Devuelve sólo datos serializables (para cruzar entre procesos):
    {"variable", "funcion_texto", "funcion_latex", "primitiva_texto",
    "primitiva_latex" (con "+ C"), "funciones_especiales", "nota"}.
    Levanta ValueError (entrada) o IntegralNoResuelta.
    """
    from sympy import Function, Integral, gamma, gammasimp, integrate, latex

    f, x = preparar_integrando(f_str, variable)
    F = integrate(f, x)

    if F.has(Integral):
        raise IntegralNoResuelta(
            "sympy no encontró una primitiva de esta función (quedó una integral sin "
            "resolver). Eso no prueba que no exista: puede no ser elemental o requerir "
            "una sustitución que el motor no encuentra."
        )
    if F.has(gamma):
        F = gammasimp(F)  # constantes como Γ(3/4)/Γ(7/4) de la integral de Fresnel

    elementales, especiales = _funciones_admitidas()
    usadas_especiales: List[str] = []
    ajenas = set()
    for fn in F.atoms(Function):
        if fn.func in elementales:
            continue
        if fn.func in especiales:
            usadas_especiales.append(fn.func.__name__)
        elif isinstance(fn, gamma) and fn.args[0].is_number:
            continue
        else:
            ajenas.add(fn.func.__name__)
    if ajenas:
        tramos = "Piecewise" in ajenas
        raise IntegralNoResuelta(
            "sympy no encontró una primitiva expresable con las funciones admitidas: "
            + ("la que encontró es por tramos." if tramos
               else f"usa {', '.join(sorted(ajenas))}.")
        )

    F = _con_valor_absoluto(F, f)
    _verificar_primitiva(F, f, x)

    usadas_especiales = sorted(set(usadas_especiales))
    nota = None
    if usadas_especiales:
        nota = (
            "La primitiva usa funciones especiales (" + ", ".join(usadas_especiales)
            + "): no se expresa con funciones elementales, pero es una primitiva "
            "correcta (F' = f)."
        )
    estilo = {"ln_notation": True, "inv_trig_style": "full"}
    cuerpo = latex(F, **estilo)
    return {
        "variable": variable,
        "funcion_texto": str(f),
        "funcion_latex": latex(f, **estilo),
        "primitiva_texto": str(F),
        "primitiva_latex": "C" if F == 0 else f"{cuerpo} + C",
        "funciones_especiales": usadas_especiales,
        "definiciones": {n: FUNCIONES_ESPECIALES[n] for n in usadas_especiales},
        "nota": nota,
    }


def _trabajador_integral(conexion, f_str: str, variable: str) -> None:
    """Punto de entrada del proceso hijo: manda el resultado por el pipe."""
    try:
        conexion.send(("ok", integrar_simbolica(f_str, variable)))
    except ValueError as exc:
        conexion.send(("entrada", str(exc)))
    except IntegralNoResuelta as exc:
        conexion.send(("no_resuelta", str(exc)))
    except Exception as exc:  # cualquier otra falla de sympy: no resuelta
        conexion.send(("no_resuelta", f"sympy no pudo completar la integral ({type(exc).__name__})."))
    finally:
        conexion.close()


def integrar_con_limite(f_str: str, variable: str = "x", segundos: float = None) -> Dict[str, Any]:
    """integrar_simbolica en un proceso aparte, cortado a `segundos`.

    Valida la entrada antes (rápido, sin proceso). Si el cálculo no termina
    a tiempo, termina el proceso (terminate y, si hiciera falta, kill) y
    levanta CalculoDemasiadoCostoso. Si ya hay INTEGRALES_SIMULTANEAS
    corriendo, espera un turno un segundo y si no lo hay, también.
    """
    import multiprocessing

    if segundos is None:
        segundos = TIEMPO_MAXIMO_INTEGRAL_S
    preparar_integrando(f_str, variable)

    if not _EN_CURSO.acquire(timeout=_ESPERA_TURNO_S):
        raise ServidorOcupado(
            "Hay otras integrales en cálculo; probá de nuevo en unos segundos."
        )
    try:
        contexto = multiprocessing.get_context("spawn")
        recibir, enviar = contexto.Pipe(duplex=False)
        proceso = contexto.Process(target=_trabajador_integral, args=(enviar, f_str, variable),
                                   daemon=True)
        proceso.start()
        enviar.close()
        try:
            respuesta = recibir.recv() if recibir.poll(segundos) else None
        except EOFError:
            respuesta = ("no_resuelta", "El cálculo terminó sin devolver un resultado.")
        finally:
            recibir.close()
            proceso.join(0.5)
            if proceso.is_alive():
                proceso.terminate()
                proceso.join(2)
            if proceso.is_alive():
                proceso.kill()
                proceso.join(2)
    finally:
        _EN_CURSO.release()

    if respuesta is None:
        raise CalculoDemasiadoCostoso(
            f"La integral no se resolvió dentro del tiempo máximo ({segundos:g} s): el cálculo "
            "es demasiado costoso para el motor simbólico. Probá simplificar la expresión."
        )
    tipo, contenido = respuesta
    if tipo == "ok":
        return contenido
    if tipo == "entrada":
        raise ValueError(contenido)
    raise IntegralNoResuelta(contenido)


__all__ = [
    "CalculoDemasiadoCostoso",
    "IntegralNoResuelta",
    "LARGO_MAXIMO",
    "ServidorOcupado",
    "TIEMPO_MAXIMO_INTEGRAL_S",
    "derivar_simbolica",
    "integrar_con_limite",
    "integrar_simbolica",
    "preparar_integrando",
    "validar_variable",
]
