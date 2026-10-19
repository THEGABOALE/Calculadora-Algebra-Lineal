"""
CÁLCULO DE ERRORES: absoluto y relativo (issue #9) y acumulado (issue #8).

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

ERROR ACUMULADO (interés compuesto)

Dos trayectorias desde el mismo monto inicial P, con tasa r por período
expresada como fracción decimal (0.05 = 5 %):

    real:        I_k = r·R_{k-1}        R_k = R_{k-1} + I_k     (= P(1+r)^k, exacto)
    aproximada:  Ĩ_k = q(r·A_{k-1})     A_k = A_{k-1} + Ĩ_k     (R_0 = A_0 = P)

q es la operación que se estudia, aplicada al INTERÉS de cada período antes
de sumarlo al saldo (como un banco que acredita intereses en centavos):
"trunc" trunca hacia cero (ROUND_DOWN: -1.25 -> -1.2, no -1.3) y "round"
redondea mitad hacia arriba, lejos de cero (ROUND_HALF_UP: 1.25 -> 1.3,
-1.25 -> -1.3), a `decimales_aproximacion` decimales. La trayectoria
aproximada se alimenta de su propio saldo anterior A_{k-1}, nunca se
recalcula desde P; la real no tiene ninguna aproximación intermedia.

Por iteración:

    diferencia_k      = I_k - Ĩ_k      cuánto crece la brecha en ESTE período
    error_acumulado_k = R_k - A_k      error TOTAL hasta ahora = Σ diferencia_j

y la diferencia se descompone en

    error_local_k     = r·A_{k-1} - Ĩ_k    lo que q quitó (o agregó) en este período
    error_propagado_k = r·E_{k-1}          interés que no generó el error anterior

así que E_k = (1+r)·E_{k-1} + error_local_k: el error acumulado no es sólo
la suma de los redondeos, porque cada centavo perdido deja de ganar interés
en los períodos siguientes. (La implementación del repositorio de referencia
calculaba el "monto real" de cada fila sobre el saldo ya aproximado, así que
su error acumulado sólo sumaba los errores locales y omitía esa propagación.)

Todo se calcula en Decimal exacto (salvo la operación q, que es el redondeo
que se estudia); los límites de entrada aseguran que la precisión del
contexto alcanza, y un trap de Inexact lo verifica en vez de suponerlo.

Sin dependencias: sólo la biblioteca estándar (el CLI no paga sympy por
importar este módulo).
"""

from __future__ import annotations

from decimal import (
    ROUND_DOWN,
    ROUND_HALF_UP,
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    Inexact,
    InvalidOperation,
    Overflow,
)
from typing import Any, Dict, List, Optional, Tuple, Union

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


# ---------------------------------------------------------------------------
# Error acumulado
# ---------------------------------------------------------------------------

MODOS_APROXIMACION: Dict[str, Any] = {"trunc": ROUND_DOWN, "round": ROUND_HALF_UP}
_TEXTO_MODO = {"trunc": "truncar", "round": "redondear"}

ITERACIONES_MAXIMAS = 50
DECIMALES_APROXIMACION_MAXIMOS = 10
DECIMALES_PRESENTACION_POR_DEFECTO = 4
MONTO_MAXIMO = Decimal("1e15")
TASA_MAXIMA = Decimal(1)  # 100 % por período
DECIMALES_ENTRADA_MAXIMOS = 10

# Con los límites de arriba R_k tiene a lo sumo ~26 + 50·11 cifras: 2000 de
# precisión sobra, y el trap de Inexact garantiza que ninguna operación de
# las trayectorias redondeó (si pasara, se reporta como ValueError).
_ACUMULADO = Context(prec=2000, rounding=ROUND_HALF_UP,
                     traps=[Inexact, InvalidOperation, Overflow, DivisionByZero])
# q sí descarta cifras (es lo que se estudia): sin trap de Inexact.
_APROXIMAR = Context(prec=2000, rounding=ROUND_HALF_UP,
                     traps=[InvalidOperation, Overflow, DivisionByZero])


def _cifras_decimales(valor: Decimal) -> int:
    exponente = valor.normalize(_APROXIMAR).as_tuple().exponent
    return max(0, -exponente)


def leer_monto(texto: Numero) -> Decimal:
    valor = leer_decimal(texto, "monto inicial")
    if valor.copy_abs() > MONTO_MAXIMO:
        raise ValueError("El monto inicial no puede superar 1e15 en valor absoluto.")
    if _cifras_decimales(valor) > DECIMALES_ENTRADA_MAXIMOS:
        raise ValueError(f"El monto inicial admite a lo sumo {DECIMALES_ENTRADA_MAXIMOS} decimales.")
    return valor


def leer_tasa(texto: Numero) -> Decimal:
    valor = leer_decimal(texto, "valor de la tasa")
    if not 0 <= valor <= TASA_MAXIMA:
        raise ValueError(
            "La tasa se escribe como fracción decimal por período (0.05 = 5 %) "
            "y debe estar entre 0 y 1."
        )
    if _cifras_decimales(valor) > DECIMALES_ENTRADA_MAXIMOS:
        raise ValueError(f"La tasa admite a lo sumo {DECIMALES_ENTRADA_MAXIMOS} decimales.")
    return valor


def _validar_entero(valor: int, minimo: int, maximo: int, descripcion: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{descripcion} debe ser un número entero.")
    if not minimo <= valor <= maximo:
        raise ValueError(f"{descripcion} debe estar entre {minimo} y {maximo}.")


def aproximar(valor: Decimal, decimales: int, modo: str) -> Decimal:
    """q: trunca hacia cero ("trunc") o redondea mitad-arriba ("round")."""
    if modo not in MODOS_APROXIMACION:
        raise ValueError(f"Modo desconocido: {modo!r}. Los admitidos son: trunc, round.")
    cuanto = Decimal(1).scaleb(-decimales, context=_APROXIMAR)
    return valor.quantize(cuanto, rounding=MODOS_APROXIMACION[modo], context=_APROXIMAR)


def texto_operacion(modo: str, decimales: int) -> str:
    return f"{_TEXTO_MODO[modo]} a {decimales} decimal{'es' if decimales != 1 else ''}"


def calcular_error_acumulado(
    monto_inicial: Numero,
    tasa: Numero,
    iteraciones: int,
    modo: str = "trunc",
    decimales_aproximacion: int = 2,
) -> Dict[str, Any]:
    """Tabla de las dos trayectorias (ver el docstring del módulo).

    Devuelve {"monto_inicial", "tasa", "iteraciones", "modo",
    "decimales_aproximacion", "filas", "resumen"}; cada fila tiene, en
    Decimal exacto: iteracion, monto_anterior_real, monto_anterior_aprox,
    interes_real, interes_aprox, monto_real, monto_aprox, diferencia,
    error_local, error_propagado, error_acumulado.

    Levanta ValueError con un mensaje para el usuario si alguna entrada está
    fuera del dominio admitido.
    """
    if modo not in MODOS_APROXIMACION:
        raise ValueError(f"Modo desconocido: {modo!r}. Los admitidos son: trunc, round.")
    _validar_entero(iteraciones, 1, ITERACIONES_MAXIMAS, "La cantidad de iteraciones")
    _validar_entero(decimales_aproximacion, 0, DECIMALES_APROXIMACION_MAXIMOS,
                    "La cantidad de decimales de la aproximación")
    P = leer_monto(monto_inicial)
    r = leer_tasa(tasa)

    c = _ACUMULADO
    real = aprox = P
    error = Decimal(0)
    filas: List[Dict[str, Any]] = []
    try:
        for k in range(1, iteraciones + 1):
            interes_real = c.multiply(r, real)
            base_aprox = c.multiply(r, aprox)
            interes_aprox = aproximar(base_aprox, decimales_aproximacion, modo)
            nuevo_real = c.add(real, interes_real)
            nuevo_aprox = c.add(aprox, interes_aprox)
            nuevo_error = c.subtract(nuevo_real, nuevo_aprox)
            filas.append({
                "iteracion": k,
                "monto_anterior_real": real,
                "monto_anterior_aprox": aprox,
                "interes_real": interes_real,
                "interes_aprox": interes_aprox,
                "monto_real": nuevo_real,
                "monto_aprox": nuevo_aprox,
                "diferencia": c.subtract(interes_real, interes_aprox),
                "error_local": c.subtract(base_aprox, interes_aprox),
                "error_propagado": c.multiply(r, error),
                "error_acumulado": nuevo_error,
            })
            real, aprox, error = nuevo_real, nuevo_aprox, nuevo_error
    except DecimalException as exc:  # no debería ocurrir con los límites de entrada
        raise ValueError(f"El cálculo excede la precisión admitida: {exc!r}") from None

    return {
        "monto_inicial": P,
        "tasa": r,
        "iteraciones": iteraciones,
        "modo": modo,
        "decimales_aproximacion": decimales_aproximacion,
        "filas": filas,
        "resumen": {
            "monto_final_real": real,
            "monto_final_aprox": aprox,
            "error_acumulado_final": error,
        },
    }


def texto_fijo(valor: Decimal, decimales: int) -> str:
    """Valor exacto con `decimales` decimales si los tiene; si no, completo.

    Para la trayectoria aproximada, que ya está redondeada: nunca agrega "≈"
    porque nunca redondea al mostrar.
    """
    if valor == 0:
        valor = valor.copy_abs()  # sin "-0.00"
    cuanto = Decimal(1).scaleb(-decimales, context=_APROXIMAR)
    fijo = valor.quantize(cuanto, context=_APROXIMAR)
    if fijo == valor:
        return format(fijo, "f")
    return texto_exacto(valor)


def texto_compacto(valor: Decimal) -> str:
    """Valor exacto sin ceros a la derecha (0.0010 -> 0.001)."""
    if valor == 0:
        return "0"
    return texto_exacto(valor.normalize(_APROXIMAR))


__all__ = [
    "DECIMALES_POR_DEFECTO",
    "DECIMALES_MAXIMOS",
    "DECIMALES_APROXIMACION_MAXIMOS",
    "DECIMALES_PRESENTACION_POR_DEFECTO",
    "ITERACIONES_MAXIMAS",
    "MODOS_APROXIMACION",
    "aproximar",
    "calcular_error_absoluto_relativo",
    "calcular_error_acumulado",
    "leer_monto",
    "leer_tasa",
    "texto_compacto",
    "texto_fijo",
    "texto_operacion",
    "leer_decimal",
    "texto_exacto",
    "texto_redondeado",
    "validar_decimales",
]
