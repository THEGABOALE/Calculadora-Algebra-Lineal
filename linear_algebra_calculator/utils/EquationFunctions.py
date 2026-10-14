from constants.SubDigits import SUBDIGITS
from fractions import Fraction
from math import isfinite, ulp

def num_to_sub(num: int) -> str:
    ''' Convertir un numero en subindice unicode '''
    if num < 0:
        raise ValueError("No se pueden convertir numeros negativos a subindice")
    return ''.join(SUBDIGITS[d] for d in str(num))

# Cifras significativas que un double garantiza conservar (DBL_DIG): todo
# decimal de hasta 15 cifras vuelve idéntico tras pasar por float. Si la
# representación más corta de un float (repr) tiene <= 15 cifras, ESE decimal
# es el valor guardado y se muestra tal cual. Si necesita 16-17, el valor no
# es un decimal "limpio": es ruido alrededor de un número simple
# (1.9999999999999998) o un valor sin expresión decimal corta (pi).
_CIFRAS_EXACTAS = 15
# Distancia máxima, en ulps (unidades en la última posición del float), para
# leer un valor "sucio" como el entero o la fracción simple que tiene al lado.
# Medido sobre las soluciones e inversas de 3.000 sistemas enteros 2x2-4x4:
# Cramer da resultados exactos; Gauss-Jordan y la inversa dejan ruido con
# p99 ~35 y p99.9 ~470 ulps. 128 cubre el 99.7% de ese ruido y, sobre 200.000
# floats aleatorios, no aceptó ninguna fracción falsa (con 1024 hubo 16).
# Relativamente son ~3e-14: nunca un dígito que el double muestre limpio.
_ULPS_RUIDO = 128
# Fracción "legible": denominador <= 10000 y numerador <= 1e6. El 99.4% de las
# soluciones exactas de esos sistemas enteros tiene denominador <= 10000 (con
# 1000 sólo el 83%), e incluye 1/1024, 1/2048, 1/4096. El numerador acotado
# evita mostrar 1000000000.25 como 4000000001/4.
_DENOMINADOR_MAX = 10_000
_NUMERADOR_MAX = 10**6
# 2**53: a partir de acá todos los float son enteros; se escriben con repr.
_ENTERO_EXACTO_MAX = 2.0 ** 53
# Cifras de una aproximación visible ("≈3.141592654").
_CIFRAS_APROX = 10


def _cifras_significativas(texto: str) -> int:
    mantisa = texto.lstrip("-").split("e")[0].replace(".", "").lstrip("0")
    return len(mantisa.rstrip("0")) or 1


def _sin_ceros_de_exponente(texto: str) -> str:
    if "e" in texto:
        mantisa, exponente = texto.split("e")
        texto = f"{mantisa}e{int(exponente)}"
    return texto[:-2] if texto.endswith(".0") else texto


def format_number(num: float) -> str:
    ''' Formatea un número para mostrarlo en los pasos.

    Distingue tres presentaciones:

    1. EXACTA del valor guardado:
       - "0" sólo para el cero exacto. Decidir que algo "es cero" es trabajo
         del algoritmo que lo calculó (core/matrix_tools.py), no del formato.
       - Un entero, con todas sus cifras (1000000000000001 -> "1000000000000001").
       - Una fracción legible cuyo valor en float ES el guardado
         (0.5 -> "1/2", 0.1 -> "1/10", 1/1024 -> "1/1024").
       - El decimal más corto que reproduce el float, si tiene <= 15 cifras
         (1000000000.25 -> "1000000000.25", 1e-15 -> "1e-15").
    2. SIMPLIFICADA: un valor cuya representación exacta necesita 16-17
       cifras y está a <= 128 ulps de un entero, una fracción legible o un
       decimal de <= 10 cifras se muestra como ese número
       (1.9999999999999998 -> "2", 0.1 + 0.2 -> "3/10",
       1.0000000000000001e-16 -> "1e-16"). La diferencia es ruido de
       redondeo, del orden de 1e-14 relativo.
    3. APROXIMACIÓN VISIBLE: si no hay nada simple tan cerca, 10 cifras
       significativas con "≈" adelante (pi -> "≈3.141592654"). No se presenta
       como exacto algo que no lo es.

    inf / nan se devuelven como texto.

    Antes se usaba una tolerancia relativa 1e-9 sobre TODA la magnitud: a
    1e9 eso son 1.0 de margen, y 1000000000.25 salía "1000000000"
    (y -1000000000.75 salía "-1000000001", otro entero).
    '''
    if isinstance(num, int) and not isinstance(num, bool):
        return str(num)
    num = float(num)
    if not isfinite(num):
        return str(num)
    if num == 0:
        return "0"

    # 1. Enteros: exactos, con todas sus cifras mientras sean exactos.
    if num.is_integer():
        if abs(num) < _ENTERO_EXACTO_MAX:
            return str(int(num))
        return _sin_ceros_de_exponente(repr(num))

    texto_exacto = repr(num)
    limpio = _cifras_significativas(texto_exacto) <= _CIFRAS_EXACTAS
    margen = _ULPS_RUIDO * ulp(num)

    # 2. Entero cercano (sólo si el valor es "sucio").
    if not limpio and abs(num) < _ENTERO_EXACTO_MAX:
        entero = round(num)
        if entero != 0 and abs(num - entero) <= margen:
            return str(int(entero))

    # 3. Fracción legible: exacta, o cercana si el valor es "sucio".
    frac = Fraction(num).limit_denominator(_DENOMINADOR_MAX)
    if frac != 0 and abs(frac.numerator) <= _NUMERADOR_MAX:
        distancia = abs(num - float(frac))
        if distancia == 0 or (not limpio and distancia <= margen):
            return str(frac)

    # 4. Decimal exacto corto.
    if limpio:
        return _sin_ceros_de_exponente(texto_exacto)

    # 5. Decimal corto cercano: ruido alrededor de un decimal de <= 10 cifras
    #    (det de diag(1e-8, 1e-8) = 1.0000000000000001e-16 -> "1e-16"). El
    #    tope de 10 cifras importa: con 14, CUALQUIER número quedaría a menos
    #    de 128 ulps de su redondeo (pi -> "3.1415926535898", presentado como
    #    exacto). Con 10, sobre 200.000 floats aleatorios sólo un 0.017% se
    #    acerca por casualidad, y ninguna constante (pi, e, raíces...).
    for cifras in range(1, _CIFRAS_APROX + 1):
        corto = f"{num:.{cifras}g}"
        if abs(float(corto) - num) <= margen:
            return _sin_ceros_de_exponente(corto)

    # 6. Aproximación visible.
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
