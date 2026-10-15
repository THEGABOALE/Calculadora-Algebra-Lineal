"""
ERROR ABSOLUTO Y RELATIVO

    Ea = |m - m~|                      (error absoluto)
    Er = |m - m~| / |m|,   m != 0      (error relativo)

m es el valor verdadero y m~ la aproximación. Los dos errores son siempre
>= 0, sea cual sea el signo de m y m~. Si m = 0 el error relativo no está
definido (dividiría entre cero): se devuelve None con una nota, nunca un
número inventado.

ARITMÉTICA DECIMAL: los valores llegan como texto y se leen con
decimal.Decimal, no con float. Un cálculo de error no puede introducir el
error de representación que pretende medir: con float, 0.3 - 0.1 da
0.19999999999999998; con Decimal da 0.2. La resta es exacta (el contexto
tiene precisión de sobra para las magnitudes admitidas); el cociente de Er se
calcula con PRECISION_RELATIVO cifras significativas.

PRESENTACIÓN: `decimales` sólo controla cómo se muestra el resultado, no la
precisión interna. Mismo criterio que utils/EquationFunctions.format_number:
un valor que se muestra redondeado lleva "≈"; uno que se muestra exacto, no.
Y un error distinto de cero nunca se muestra como 0: si con `decimales`
quedaría en 0, se muestra en notación científica.

Sin dependencias: sólo la biblioteca estándar (el CLI no paga sympy por
importar este módulo).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Context, Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple, Union

DECIMALES_POR_DEFECTO = 6
DECIMALES_MAXIMOS = 15

# Límites de entrada: suficientes para cualquier dato de clase y
# acotados para que la resta exacta no necesite una precisión ilimitada.
EXPONENTE_MAXIMO = 100  # |m| y |m~| entre 1e-100 y 1e100 (o 0)
_MAGNITUD_MAXIMA = Decimal(1).scaleb(EXPONENTE_MAXIMO)
_MAGNITUD_MINIMA = Decimal(1).scaleb(-EXPONENTE_MAXIMO)
CIFRAS_MAXIMAS = 50

PRECISION_RELATIVO = 50
# Resta exacta: alcanza con cubrir del dígito más alto (1e100) al más bajo
# (1e-100 con 50 cifras), con margen.
_EXACTO = Context(prec=400, rounding=ROUND_HALF_UP)
_RELATIVO = Context(prec=PRECISION_RELATIVO, rounding=ROUND_HALF_UP)

Numero = Union[str, int, Decimal]

FORMULA_ABSOLUTO = "|m - m̃|"
FORMULA_RELATIVO = ("|m - m̃|", "|m|")


def leer_decimal(texto: Numero, nombre: str) -> Decimal:
    """Convierte la entrada en un Decimal finito, o levanta ValueError.

    Acepta enteros, decimales con punto y notación científica ("1e-5").
    Rechaza vacío, texto no numérico, NaN, infinitos, fracciones "a/b" (no
    tienen una expresión decimal exacta en general), coma decimal y
    magnitudes fuera de los límites del módulo.
    """
    if isinstance(texto, bool):
        raise ValueError(f"El {nombre} debe ser un número, no un valor lógico.")
    crudo = str(texto).strip()
    if not crudo:
        raise ValueError(f"Ingresá el {nombre}.")
    try:
        valor = Decimal(crudo)
    except InvalidOperation:
        raise ValueError(
            f"El {nombre} debe ser un número (por ejemplo 3.14, -2 o 1e-5); se recibió {crudo!r}."
        ) from None
    if not valor.is_finite():
        raise ValueError(f"El {nombre} debe ser un número finito; se recibió {crudo!r}.")
    # Comparación directa con los límites, no por exponente: adjusted()
    # vale 100 tanto para 1e100 como para 9e100.
    magnitud = valor.copy_abs()
    if valor != 0 and not _MAGNITUD_MINIMA <= magnitud <= _MAGNITUD_MAXIMA:
        raise ValueError(
            f"El {nombre} está fuera del rango admitido "
            f"(entre 1e-{EXPONENTE_MAXIMO} y 1e{EXPONENTE_MAXIMO} en valor absoluto)."
        )
    if len(valor.as_tuple().digits) > CIFRAS_MAXIMAS:
        raise ValueError(f"El {nombre} tiene más de {CIFRAS_MAXIMAS} cifras significativas.")
    return valor


def validar_decimales(decimales: int) -> None:
    if isinstance(decimales, bool) or not isinstance(decimales, int):
        raise ValueError("La cantidad de decimales debe ser un entero.")
    if not 0 <= decimales <= DECIMALES_MAXIMOS:
        raise ValueError(f"La cantidad de decimales debe estar entre 0 y {DECIMALES_MAXIMOS}.")


def texto_exacto(valor: Decimal) -> str:
    """El valor tal cual, sin redondear: notación fija salvo magnitudes extremas."""
    if valor == 0:
        return "0"
    if -12 <= valor.adjusted() <= 20:
        return format(valor, "f")
    return format(valor, "E")


def texto_redondeado(valor: Decimal, decimales: int) -> str:
    """`valor` con `decimales` decimales; "≈ " si eso no es el valor exacto.

    Si el redondeo daría 0 para un valor distinto de cero, se usa notación
    científica con `decimales` decimales en la mantisa.

    Todo el redondeo usa el contexto del módulo (ROUND_HALF_UP), nunca el
    contexto decimal global: el resultado no depende de quién lo haya
    cambiado (format() con "E" redondearía con el global, ROUND_HALF_EVEN
    por defecto: 2.5e-7 daría 2E-7 en vez de 3E-7).
    """
    cuanto = Decimal(1).scaleb(-decimales, context=_EXACTO)
    fijo = valor.quantize(cuanto, context=_EXACTO)
    if fijo == 0 and valor != 0:
        exponente = valor.adjusted()
        mantisa = valor.scaleb(-exponente, context=_EXACTO).quantize(cuanto, context=_EXACTO)
        if mantisa.copy_abs() >= 10:  # 9.96 con 1 decimal -> 10.0: renormalizar
            exponente += 1
            mantisa = valor.scaleb(-exponente, context=_EXACTO).quantize(cuanto, context=_EXACTO)
        texto = f"{format(mantisa, 'f')}E{exponente:+d}"
        mostrado = mantisa.scaleb(exponente, context=_EXACTO)
    else:
        texto = format(fijo, "f")
        mostrado = fijo
    return texto if mostrado == valor else f"≈ {texto}"


def _sustitucion(m: Decimal, mt: Decimal) -> Tuple[str, str]:
    """Numerador |m - m~| y denominador |m| con los valores ingresados."""
    m_txt, mt_txt = texto_exacto(m), texto_exacto(mt)
    if mt < 0:
        mt_txt = f"({mt_txt})"
    return f"|{m_txt} - {mt_txt}|", f"|{m_txt}|"


def calcular_error_absoluto_relativo(
    valor_verdadero: Numero,
    valor_aproximado: Numero,
    decimales: int = DECIMALES_POR_DEFECTO,
) -> Dict[str, Any]:
    """Error absoluto y relativo de `valor_aproximado` respecto de `valor_verdadero`.

    Devuelve:
        {
          "valor_verdadero": Decimal, "valor_aproximado": Decimal, "decimales": int,
          "error_absoluto": {"valor", "texto", "formula", "sustitucion"},
          "error_relativo": {"valor", "texto", "porcentaje", "formula",
                             "sustitucion", "nota"},
        }
    `valor`/`texto`/`porcentaje` del relativo son None si m = 0 (`nota`
    explica por qué); si no, `nota` es None.

    Levanta ValueError si alguna entrada no es un número válido o si
    `decimales` está fuera de [0, DECIMALES_MAXIMOS].
    """
    validar_decimales(decimales)
    m = leer_decimal(valor_verdadero, "valor verdadero")
    mt = leer_decimal(valor_aproximado, "valor aproximado")

    ea = _EXACTO.abs(_EXACTO.subtract(m, mt))
    numerador, denominador = _sustitucion(m, mt)

    er: Optional[Decimal]
    nota: Optional[str]
    if m == 0:
        er, texto_er, porcentaje, nota = None, None, None, (
            "Indefinido: el valor verdadero m es 0 y Er = |m - m̃| / |m| "
            "dividiría entre cero. Con m = 0 sólo tiene sentido el error absoluto."
        )
    else:
        er = _RELATIVO.divide(ea, abs(m))
        texto_er = texto_redondeado(er, decimales)
        porcentaje = f"{texto_redondeado(_RELATIVO.multiply(er, Decimal(100)), decimales)} %"
        nota = None

    return {
        "valor_verdadero": m,
        "valor_aproximado": mt,
        "decimales": decimales,
        "error_absoluto": {
            "valor": ea,
            "texto": texto_redondeado(ea, decimales),
            "formula": FORMULA_ABSOLUTO,
            "sustitucion": numerador,
        },
        "error_relativo": {
            "valor": er,
            "texto": texto_er,
            "porcentaje": porcentaje,
            "formula": FORMULA_RELATIVO,
            "sustitucion": (numerador, denominador),
            "nota": nota,
        },
    }


__all__ = [
    "DECIMALES_POR_DEFECTO",
    "DECIMALES_MAXIMOS",
    "calcular_error_absoluto_relativo",
    "leer_decimal",
    "texto_exacto",
    "texto_redondeado",
    "validar_decimales",
]
