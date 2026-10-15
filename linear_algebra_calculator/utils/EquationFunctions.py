from constants.SubDigits import SUBDIGITS
from decimal import Decimal
from fractions import Fraction
from math import isfinite, ulp

def num_to_sub(num: int) -> str:
    ''' Convertir un numero en subindice unicode '''
    if num < 0:
        raise ValueError("No se pueden convertir numeros negativos a subindice")
    return ''.join(SUBDIGITS[d] for d in str(num))

# Política de presentación (ver documentation/CriterioNumerico.md, sección 5):
#
#   EXACTA (sin marca)  el texto, leído de vuelta, da EL MISMO float.
#   ≈ ...               cualquier otra cosa: el texto no es el valor guardado.
#
# El formateador no puede distinguir ruido de redondeo de un dato: un usuario
# que tipea 10000000000.00006 obtiene un float cuya representación necesita
# 16 cifras, igual que el ruido 1.9999999999999998. Por eso ninguna
# simplificación se presenta sin "≈": mostrar "10000000000" o "2" sin marca
# sería afirmar que el valor es ese número, y no lo es.

# DBL_DIG: todo decimal de hasta 15 cifras vuelve idéntico tras pasar por
# float. Si repr(x) tiene <= 15 cifras, ese decimal ES el valor guardado.
_CIFRAS_EXACTAS = 15
# Distancia máxima, en ulps, para ofrecer "≈ número simple" (≈2, ≈3/10) en
# vez de "≈ 10 cifras". Medido sobre 3.000 sistemas enteros 2x2-4x4 contra la
# solución racional exacta: Cramer exacto; Gauss-Jordan e inversa con ruido
# p99 ~35, p99.9 ~470 ulps; 128 cubre el 99.7%. Sobre 200.000 floats
# aleatorios, 128 ulps con denominador <= 10000 no propuso ninguna fracción
# falsa (con 1024 hubo 16), ni para pi, e, raíces, ln 2 o phi.
_ULPS_RUIDO = 128
# Fracción "legible": denominador <= 10000 y |numerador| <= 1e6. El 99.4% de
# las soluciones exactas de esos sistemas tiene denominador <= 10000 (con 1000
# sólo el 83%); incluye 1/1024, 1/2048, 1/4096. El numerador acotado evita
# mostrar 1000000000.25 como 4000000001/4.
_DENOMINADOR_MAX = 10_000
_NUMERADOR_MAX = 10**6
# 2**53: a partir de acá todos los float son enteros; se escriben con repr.
_ENTERO_EXACTO_MAX = 2.0 ** 53
# Cifras de "≈ decimal": tanto del decimal corto cercano como del último
# recurso. Con 14, cualquier número quedaría a < 128 ulps de su redondeo y
# pi tendría un "decimal corto" de 14 cifras; con 10, sobre 200.000 floats
# aleatorios sólo un 0.017% cae tan cerca de un decimal corto por casualidad.
_CIFRAS_APROX = 10


def _cifras_significativas(texto: str) -> int:
    mantisa = texto.lstrip("-").split("e")[0].replace(".", "").lstrip("0")
    return len(mantisa.rstrip("0")) or 1


def _sin_ceros_de_exponente(texto: str) -> str:
    if "e" in texto:
        mantisa, exponente = texto.split("e")
        texto = f"{mantisa}e{int(exponente)}"
    return texto[:-2] if texto.endswith(".0") else texto


def _fraccion_legible(frac: Fraction) -> bool:
    return frac != 0 and frac.denominator <= _DENOMINADOR_MAX and abs(frac.numerator) <= _NUMERADOR_MAX


def format_number(num: float) -> str:
    ''' Formatea un número para mostrarlo en los pasos.

    EXACTA (sin marca): lo que se lee es el valor guardado -- el texto vuelve
    al mismo float. En este orden de preferencia:
      - "0" para el cero exacto (decidir que algo "es cero" es trabajo del
        algoritmo, ver core/matrix_tools.py, no del formato);
      - un entero con todas sus cifras (1000000000000001);
      - una fracción legible cuyo float ES el valor (1/2, 1/3, 1/10, 1/1024);
      - el decimal más corto que reproduce el float (repr) si tiene <= 15
        cifras (1000000000.25, 1e-15), o si el valor es EXACTAMENTE un
        racional de denominador <= 10000 aunque necesite 16-17 cifras
        (1000000000000000.5 = 2000000000000001/2): eso es un dato exacto,
        no ruido de nada, y se muestra completo.

    APROXIMADA ("≈"): cualquier otro valor. Si hay un entero, una fracción
    legible o un decimal de <= 10 cifras a <= 128 ulps, se muestra ese
    número marcado (1.9999999999999998 -> "≈2", 0.1 + 0.2 -> "≈3/10",
    10000000000.00006 -> "≈10000000000"); si no, 10 cifras significativas
    (pi -> "≈3.141592654").

    inf / nan se devuelven como texto.
    '''
    if isinstance(num, int) and not isinstance(num, bool):
        return str(num)
    num = float(num)
    if not isfinite(num):
        return str(num)
    if num == 0:
        return "0"

    # --- Exacta ------------------------------------------------------------
    if num.is_integer():
        if abs(num) < _ENTERO_EXACTO_MAX:
            return str(int(num))
        return _sin_ceros_de_exponente(repr(num))

    cercana = Fraction(num).limit_denominator(_DENOMINADOR_MAX)
    if _fraccion_legible(cercana) and float(cercana) == num:
        return str(cercana)

    texto_exacto = repr(num)
    if _cifras_significativas(texto_exacto) <= _CIFRAS_EXACTAS:
        return _sin_ceros_de_exponente(texto_exacto)
    if Fraction(num).denominator <= _DENOMINADOR_MAX:
        # Racional exacto de denominador chico (n + 1/2, n + 3/8...): dato,
        # no ruido. Se muestra su expansión decimal EXACTA (finita: el
        # denominador es una potencia de 2 <= 8192), no repr: repr de
        # 1000000000000000.25 es "1000000000000000.2", que vuelve al mismo
        # float pero no es el valor guardado.
        return format(Decimal(num), "f")

    # --- Aproximada: número simple cercano, marcado -------------------------
    margen = _ULPS_RUIDO * ulp(num)
    if abs(num) < _ENTERO_EXACTO_MAX:
        entero = round(num)
        if entero != 0 and abs(num - entero) <= margen:
            return "≈" + str(int(entero))
    if _fraccion_legible(cercana) and abs(num - float(cercana)) <= margen:
        return "≈" + str(cercana)
    for cifras in range(1, _CIFRAS_APROX + 1):
        corto = f"{num:.{cifras}g}"
        if abs(float(corto) - num) <= margen:
            return "≈" + _sin_ceros_de_exponente(corto)

    # --- Aproximada: 10 cifras ----------------------------------------------
    return "≈" + _sin_ceros_de_exponente(f"{num:.{_CIFRAS_APROX}g}")

def parse_fraction(value: str) -> float:
    if "/" in value:
        try:
            num, den = value.split("/")
            return float(num) / float(den)
        except ZeroDivisionError:
            raise ValueError("Denominador no puede ser 0")
        except Exception:
            raise ValueError("Fraccion invalida")
    return float(value)
