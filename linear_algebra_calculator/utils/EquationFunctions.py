from constants.SubDigits import SUBDIGITS
from fractions import Fraction
from math import isfinite

def num_to_sub(num: int) -> str:
    ''' Convertir un numero en subindice unicode '''
    if num < 0:
        raise ValueError("No se pueden convertir numeros negativos a subindice")
    return ''.join(SUBDIGITS[d] for d in str(num))

# Tolerancia RELATIVA para decidir que un float "es" un entero o una fracción
# simple: absorbe el redondeo de unas pocas operaciones (0.1 + 0.2 =
# 0.30000000000000004 -> 3/10, 1.9999999999999998 -> 2) y, por ser relativa,
# nunca convierte en 0 un número chico pero distinto de cero.
_REL_FORMATO = 1e-9
# Denominador máximo de una fracción "legible". Con el default de
# limit_denominator (10**6) pi salía como 3126535/995207: una aproximación
# presentada como si fuera un valor exacto.
_DENOMINADOR_MAX = 1000
# A partir de acá un entero se escribe en notación científica.
_ENTERO_MAX = 1e15

def format_number(num: float) -> str:
    ''' Formatea un número para mostrarlo en los pasos, en este orden:

    - "0" sólo si el valor es exactamente 0. Decidir que algo "es cero" es
      trabajo del algoritmo que lo calculó (ver el criterio de
      core/matrix_tools.py), no del formato: antes, cualquier |x| < 1e-9 se
      mostraba como "0", y det(1e-5·I) = 1e-15 aparecía como 0.
    - Entero, si el valor lo es salvo redondeo relativo (2.0000000000000004 -> "2").
    - Fracción con denominador <= 1000, si el valor la representa salvo
      redondeo relativo (0.333... -> "1/3").
    - Si no, decimal con 10 cifras significativas, en notación científica
      cuando hace falta (1e-15 -> "1e-15", pi -> "3.141592654"): una
      aproximación numérica se muestra como tal, no como una fracción enorme.
    - inf / nan se devuelven como texto en vez de reventar en int().
    '''
    if not isfinite(num):
        return str(float(num))
    if num == 0:
        return "0"
    magnitud = abs(num)
    if magnitud < _ENTERO_MAX:
        entero = round(num)
        if abs(num - entero) <= _REL_FORMATO * magnitud:
            return str(int(entero))
        frac = Fraction(num).limit_denominator(_DENOMINADOR_MAX)
        if frac != 0 and abs(num - float(frac)) <= _REL_FORMATO * magnitud:
            return str(frac)
    texto = f"{num:.10g}"
    if "e" in texto:
        mantisa, exponente = texto.split("e")
        texto = f"{mantisa}e{int(exponente)}"
    return texto

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
