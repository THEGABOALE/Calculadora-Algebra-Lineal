from fractions import Fraction
from math import isclose

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

def format_number(n: float, tolerance: float = 1e-9) -> str:
    if n is None:
        return ""
    if isinstance(n, str):
        return n
    
    # Convertir a fraccion con denominador maximo para encontrar fraccion "cercana"
    frac = Fraction(n).limit_denominator(1000)
    
    # si el numero es muy cercano a un entero
    if isclose(n, round(n), abs_tol=tolerance):
        return str(round(n))
    
    # si la fraccion es exacta
    if isclose(n, float(frac), abs_tol=tolerance):
        return str(frac)
    
    # ultimo recurso: mostrar como flotante con precision limitada
    return f"{n:.4f}".rstrip('0').rstrip('.')

def num_to_sub(n: int) -> str:
    """Convierte un entero a subíndice Unicode."""
    if n < 0:
        raise ValueError("No se pueden convertir numeros negativos a subindice")
    return "".join("₀₁₂₃₄₅₆₇₈₉"[int(d)] for d in str(n))
