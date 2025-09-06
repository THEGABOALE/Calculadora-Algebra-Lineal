from constants.SymbolsFunctions import SYMBOLS
from constants.SubDigits import SUBDIGITS
from copy import deepcopy
from symengine import diff, sympify, symbols
import re
from fractions import Fraction

def num_to_sub(num: int) -> str:
    ''' Convertir un numero en subindice unicode '''
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

def parse_equation(equation: str) -> str:
    '''
    Convertir la ecuacion de manera compatible
    - Añade * entre números y variables/funciones
    - Reemplaza simbolos y nombres por funciones matematicas
    ''' 
    # Multiplicacion implicita
    equation = re.sub(r"((\d)([a-zA-Z\(])", r"\1*\2", equation)
    
    # Reemplazo de simbolos
    equation = equation.replace('√', 'sqrt')
    equation = equation.replace('π', 'pi')
    equation = equation.replace('log', 'ln')
    equation = equation.replace('sen', 'sin')
    return equation

def evaluate_equation(equation: str, x_value: float | int) -> float | None:
    """
    Evaluar la ecacion para un valor dado de x
    Retornar el resultado, "Syntax Error" o None si hay error.
    """    
    allowed_symbols = deepcopy(SYMBOLS)
    allowed_symbols['x'] = x_value
    parsed_equation = parse_equation(equation)
    try:
        """ Evaluar la ecuacion """
        result = eval(parsed_equation, {"__builtins__": None}, allowed_symbols)
    except ValueError:
        return "Syntax Error"
    except Exception:
        return None
    return result

def derivate_equation(equation:str) -> str:
    """
    - Calcular la derivada simbolica de la ecuacion respecto a x.
    - Retornar la derivada como string o ecuaciuon original.
    """
    try: 
        symbolic_expresion = sympify(equation)
        derivate = diff(symbolic_expresion, symbols('x'))
        return str(derivate)
    except Exception:
        return equation
    
"""
CONTEXTO

- parse_equation()
Convierte una ecuación escrita como texto a una forma compatible con Python:

    - Añade el operador * entre números y variables/funciones (ejemplo: 2x → 2*x).
    - Reemplaza símbolos y nombres matemáticos por sus equivalentes en inglés (√ → sqrt, π → pi, log → ln, sen → sin).


- evaluate_equation()

Evalúa la ecuación para un valor dado de x:
    - Usa el diccionario de funciones matemáticas permitidas (SYMBOLS).
    - Parsea la ecuación con parse_equation.
    - Calcula el resultado usando eval.
    - Si hay un error de sintaxis, retorna "Syntax Error". Si ocurre otro error, retorna None. Si todo sale bien, retorna el resultado numérico.

- derivate_equation()

Calcula la derivada simbólica de la ecuación respecto a x:

    - Usa sympify y diff de symengine para obtener la derivada.
    - Si hay un error, retorna la ecuación original. Si todo sale bien, retorna la derivada como string.

"""