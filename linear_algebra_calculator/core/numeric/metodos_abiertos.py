"""
MÉTODOS ABIERTOS DE BÚSQUEDA DE RAÍCES
- Newton-Raphson
- Secante

No requieren un intervalo con cambio de signo: parten de uno o dos puntos
iniciales.

DERIVADA: Newton-Raphson usa derivada simbólica (sympy) en vez de diferencias
centrales con h=1e-8. Es exacta y no arrastra error de truncamiento. Se
conserva el parámetro `derivada` para quien quiera forzar una escrita a mano,
pero ya no hace falta pedírsela al usuario.

CRITERIO DE PARO: acá sólo aplica el error relativo porcentual entre
aproximaciones sucesivas. El criterio por longitud de intervalo que soportan
los métodos cerrados no tiene sentido sin intervalo.

DEGENERACIONES: derivada idénticamente nula, f'(x_k) = 0 en una iteración y
denominador nulo en la secante ahora levantan excepción en vez de devolver un
dict con 'advertencia'. Son condiciones donde la fórmula no está definida, no
resultados aproximados: devolver una "raíz" en ese caso era afirmar algo que
el método no calculó.
"""

from typing import Any, Dict, List, Optional

from core.numeric._expresiones import (
    a_latex,
    compilar,
    derivar,
    error_relativo as calcular_error_relativo,
    evaluar,
)

# Sufijo LaTeX de las aproximaciones según la unidad de x.
_UNIDAD_LATEX = {"rad": "", "deg": r"^\circ"}


def _validar_tolerancia(tolerancia: float) -> None:
    if tolerancia <= 0:
        raise ValueError(f"La tolerancia debe ser positiva (tolerancia={tolerancia}).")


def _conclusion(metodo: str, raiz: float, iteraciones: int, unidad: str = "") -> Dict[str, Any]:
    return {
        "raiz": raiz,
        "iteraciones": iteraciones,
        "criterio_paro": "error_relativo < tolerancia",
        "latex": (
            rf"\text{{{metodo} converge en }} {iteraciones} \text{{ iteraciones. }}"
            rf"\text{{La raíz aproximada es }} x_r = {raiz:.6f}{unidad}."
        ),
    }


def metodo_newton_raphson(
    f_str: str,
    x0: float,
    tolerancia: float,
    max_iter: int = 100,
    derivada: Optional[str] = None,
) -> Dict:
    """
    Método de Newton-Raphson para encontrar raíces.

    Fórmula: x_{n+1} = x_n - f(x_n)/f'(x_n)

    Parámetros:
    - f_str: función como string
    - x0: punto inicial
    - tolerancia: umbral del error relativo porcentual
    - max_iter: máximo número de iteraciones
    - derivada: derivada como string; si es None se deriva simbólicamente

    Levanta:
    - ValueError si la derivada es idénticamente cero (función constante)
    - ZeroDivisionError si f'(x_k) = 0 en alguna iteración
    """
    _validar_tolerancia(tolerancia)
    f, expr, x = compilar(f_str)
    fprime, dexpr = derivar(expr, x, derivada)

    historial: List[Dict] = []
    detalles: List[Dict] = []
    x_actual = float(x0)
    x_nuevo = x_actual
    error_actual = float("inf")

    for i in range(1, max_iter + 1):
        fx = evaluar(f, x_actual, f_str)
        dfx = evaluar(fprime, x_actual, f_str)

        if dfx == 0:
            raise ZeroDivisionError(
                f"En la iteración {i} se obtuvo f'(x_k) = 0, lo que produce una "
                "división entre cero en la fórmula de Newton-Raphson."
            )

        x_nuevo = x_actual - fx / dfx
        error_actual = calcular_error_relativo(x_nuevo, x_actual) if i > 1 else float("inf")

        historial.append(
            {
                "iteracion": i,
                "x": x_actual,
                "f(x)": fx,
                "f'(x)": dfx,
                "x_nuevo": x_nuevo,
                "error": error_actual,
            }
        )
        detalles.append(
            {
                "iteracion": i,
                "lineas": [
                    rf"x_{{{i}}} = {x_actual:.6f}",
                    rf"f(x_{{{i}}}) = {fx:.6e}",
                    rf"f'(x_{{{i}}}) = {dfx:.6e}",
                    rf"x_{{{i + 1}}} = x_{{{i}}} - \frac{{f(x_{{{i}}})}}{{f'(x_{{{i}}})}} = {x_nuevo:.6f}",
                ]
                + ([rf"E_a = {error_actual:.6f}\%"] if error_actual != float("inf") else []),
            }
        )

        if error_actual < tolerancia and i > 1:
            return {
                "raiz": x_nuevo,
                "iteraciones": i,
                "historial": historial,
                "error_final": error_actual,
                "metodo": "Newton-Raphson",
                "funcion_latex": a_latex(expr),
                "derivada_latex": a_latex(dexpr),
                "detalles": detalles,
                "conclusion": _conclusion("Newton-Raphson", x_nuevo, i),
            }

        x_actual = x_nuevo

    return {
        "raiz": x_nuevo,
        "iteraciones": max_iter,
        "historial": historial,
        "error_final": error_actual,
        "metodo": "Newton-Raphson",
        "funcion_latex": a_latex(expr),
        "derivada_latex": a_latex(dexpr),
        "detalles": detalles,
        "conclusion": _conclusion("Newton-Raphson", x_nuevo, max_iter),
        "advertencia": "Alcanzado número máximo de iteraciones",
    }


def metodo_secante(
    f_str: str,
    x0: float,
    x1: float,
    tolerancia: float,
    max_iter: int = 100,
    modo_angular: str = "rad",
) -> Dict:
    """
    Método de la Secante para encontrar raíces.

    Fórmula: x_{n+1} = x_n - f(x_n)·(x_n - x_{n-1}) / (f(x_n) - f(x_{n-1}))

    modo_angular="deg": los argumentos de sin/cos/tan se leen en grados, así
    que x0, x1, las aproximaciones y la raíz están en grados y cada f(x) de
    la tabla es la función evaluada en grados. "rad" (default) es el
    comportamiento de siempre.

    Levanta:
    - ValueError si modo_angular no es "rad" ni "deg"
    - ZeroDivisionError si f(x_n) - f(x_{n-1}) = 0 en alguna iteración
    """
    _validar_tolerancia(tolerancia)
    f, expr, _ = compilar(f_str, modo_angular)
    unidad = _UNIDAD_LATEX[modo_angular]

    historial: List[Dict] = []
    detalles: List[Dict] = []
    x_anterior = float(x0)
    x_actual = float(x1)
    x_nuevo = x_actual
    error_actual = float("inf")

    for i in range(1, max_iter + 1):
        fx_anterior = evaluar(f, x_anterior, f_str)
        fx_actual = evaluar(f, x_actual, f_str)

        denominador = fx_actual - fx_anterior
        if denominador == 0:
            raise ZeroDivisionError(
                f"En la iteración {i} se obtuvo f(x_n) - f(x_(n-1)) = 0: la secante "
                "es horizontal y el método no puede continuar."
            )

        x_nuevo = x_actual - fx_actual * (x_actual - x_anterior) / denominador
        fx_nuevo = evaluar(f, x_nuevo, f_str)
        error_actual = calcular_error_relativo(x_nuevo, x_actual) if i > 1 else float("inf")

        historial.append(
            {
                "iteracion": i,
                "x_{n-1}": x_anterior,
                "x_n": x_actual,
                "f(x_{n-1})": fx_anterior,
                "f(x_n)": fx_actual,
                "x_{n+1}": x_nuevo,
                "f(x_{n+1})": fx_nuevo,
                "error": error_actual,
            }
        )
        detalles.append(
            {
                "iteracion": i,
                "lineas": [
                    rf"x_{{{i + 1}}} = x_n - \frac{{f(x_n)(x_n - x_{{n-1}})}}"
                    rf"{{f(x_n) - f(x_{{n-1}})}} = {x_nuevo:.6f}{unidad}",
                    rf"f(x_n) = {fx_actual:.6e}",
                ]
                + ([rf"E_a = {error_actual:.6f}\%"] if error_actual != float("inf") else []),
            }
        )

        if error_actual < tolerancia and i > 1:
            return {
                "raiz": x_nuevo,
                "iteraciones": i,
                "historial": historial,
                "error_final": error_actual,
                "metodo": "Secante",
                "funcion_latex": a_latex(expr),
                "detalles": detalles,
                "conclusion": _conclusion("Secante", x_nuevo, i, unidad),
                "modo_angular": modo_angular,
            }

        x_anterior = x_actual
        x_actual = x_nuevo

    return {
        "raiz": x_nuevo,
        "iteraciones": max_iter,
        "historial": historial,
        "error_final": error_actual,
        "metodo": "Secante",
        "funcion_latex": a_latex(expr),
        "detalles": detalles,
        "conclusion": _conclusion("Secante", x_nuevo, max_iter, unidad),
        "advertencia": "Alcanzado número máximo de iteraciones",
        "modo_angular": modo_angular,
    }


__all__ = ["metodo_newton_raphson", "metodo_secante"]
