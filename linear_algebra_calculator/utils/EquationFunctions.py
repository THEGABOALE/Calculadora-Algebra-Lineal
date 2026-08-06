from constants.SubDigits import SUBDIGITS
from fractions import Fraction

def num_to_sub(num: int) -> str:
    ''' Convertir un numero en subindice unicode '''
    if num < 0:
        raise ValueError("No se pueden convertir numeros negativos a subindice")
    return ''.join(SUBDIGITS[d] for d in str(num))

def format_number(num: float) -> str:
    ''' Formatea numero en entero si es exacto o fraccional '''
    if abs(num - int(num)) < 1e-9:
        return str(int(num))
    else:
        frac = Fraction(num).limit_denominator()
        return str(frac)

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
