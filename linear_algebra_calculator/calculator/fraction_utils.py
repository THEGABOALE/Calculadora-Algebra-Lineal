from fractions import Fraction
from constants.SubDigits import SUBDIGITS

def parse_fraction(s: str) -> float:
    s = s.strip()
    if "/" in s:
        try:
            num, den = map(int, s.split('/', 1))
            if den == 0:
                raise ValueError("El denominador no puede ser 0")
            return num / den
        except (ValueError, TypeError):
            raise ValueError(f"No se puede convertir '{s}' a fraccion")
    else:
        try:
            return float(s)
        except (ValueError, TypeError):
            raise ValueError(f"No se puede convertir '{s}' a numero")

def format_number(num: float, tolerance: float = 1e-9) -> str:
    ''' Formatea numero en entero si es exacto o fraccional '''
    if abs(num - int(num)) < tolerance:
        return str(int(num))
    else:
        frac = Fraction(num).limit_denominator()
        return str(frac)

def num_to_sub(num: int) -> str:
    """Convierte un entero a subíndice Unicode."""
    if num < 0:
        raise ValueError("No se pueden convertir numeros negativos a subindice")
    return ''.join(SUBDIGITS[d] for d in str(num))
