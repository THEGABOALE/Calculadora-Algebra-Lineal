"""
Módulo: positional_notation.py
Propósito:
- Descomponer números en notación posicional (base 10 y base 2).
- Mostrar cada término como "digito × base^potencia" y la suma final.
- Proveer un runner interactivo para integrarlo en el `startup.py`.

Características:
- Valida entradas (decimales y enteros positivos y negativos; para binario acepta solo cadena '10101').
- Maneja números negativos mostrando el signo y descomponiendo el absoluto.
- Confirma la validez de la descomposición sumando los términos.
- Intenta reutilizar utilidades existentes (num_to_sub, format_number) si están disponibles
  en los módulos del proyecto; si no, define funciones de respaldo sencillas.

Cómo integrarlo en startup.py (ejemplo):
    from core.positional_notation import run_positional_notation_menu
    # añadir en el menú principal:
    "7": ("Notación Posicional ▸", run_positional_notation_menu),
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Union

# Intentar reutilizar utilidades del proyecto si existen
try:
    from utils.EquationFunctions import num_to_sub, format_number
except Exception:
    # DEFINICIONES DE RESPALDO
    def num_to_sub(num: int) -> str:
        SUB = "₀₁₂₃₄₅₆₇₈₉"
        return ''.join(SUB[int(d)] for d in str(num))

    def format_number(num: float) -> str:
        if abs(num - int(num)) < 1e-9:
            return str(int(num))
        # Para términos de notación posicional, mostrar fracciones simples
        from fractions import Fraction
        frac = Fraction(num).limit_denominator(1000)
        # Mostrar como fracción si el denominador es pequeño y representa una fracción común
        if frac.denominator <= 100 and abs(frac - num) < 1e-9:
            return f"{frac.numerator}/{frac.denominator}"
        # De lo contrario, mostrar como decimal
        return f"{num:.10f}".rstrip('0').rstrip('.') or '0'

MULT_SIGN = '×'  # símbolo multiplicación para salida legible

# -------------------- SUPERÍNDICES --------------------
SUPERSCRIPTS = "⁰¹²³⁴⁵⁶⁷⁸⁹"
SUPER_MINUS = '⁻'  # Símbolo de superíndice para el negativo

def to_superscript(n: int) -> str:
    if n < 0:
        # Manejar números negativos: convertir el valor absoluto y agregar SUPER_MINUS
        return SUPER_MINUS + to_superscript(-n)
    return ''.join(SUPERSCRIPTS[int(d)] for d in str(n))

# -------------------- VALIDACIÓN --------------------
def _validate_decimal(value: str) -> float:
    """Valida un número decimal (positivo o negativo)"""
    try:
        return float(value)
    except Exception:
        raise ValueError("Entrada no válida: se esperaba un número decimal.")

# -------------------- BASE 10 --------------------
def decompose_base10_decimal(n: Union[int, float, str]) -> Dict[str, Any]:
    """Descompone un número decimal (entero o decimal) en notación posicional."""
    try:
        num = float(n)
    except:
        raise ValueError("Entrada no válida: se esperaba un número decimal.")

    negative = num < 0
    num_abs = abs(num)

    # Convertir a string con precisión controlada
    str_num = f"{num_abs}"
    # Para números con muchos decimales, limitar la precisión
    if '.' in str_num and len(str_num.split('.')[1]) > 10:
        str_num = f"{num_abs:.10f}"
    
    str_num = str_num.rstrip('0').rstrip('.') if '.' in str_num else str_num
    
    if '.' in str_num:
        int_str, frac_str = str_num.split('.')
        # Tomar solo los dígitos fraccionarios significativos (máximo 8)
        frac_str = frac_str[:8]
    else:
        int_str, frac_str = str_num, ''

    int_digits = [int(d) for d in int_str] if int_str else [0]
    frac_digits = [int(d) for d in frac_str] if frac_str else []

    terms: List[Tuple[int, int, float]] = []
    parts: List[str] = []
    total = 0

    # Parte entera
    L = len(int_digits)
    for i, d in enumerate(int_digits):
        power = L - i - 1
        val = d * (10 ** power)
        terms.append((d, power, val))
        parts.append(f"{d}{MULT_SIGN}10{to_superscript(power)}")
        total += val

    # Parte decimal (solo dígitos significativos)
    for i, d in enumerate(frac_digits):
        power = -(i + 1)
        val = d * (10 ** power)
        terms.append((d, power, val))
        parts.append(f"{d}{MULT_SIGN}10{to_superscript(power)}")
        total += val

    expr = " + ".join(parts)
    full = f"{'-' if negative else ''}{n} = {expr}"

    return {
        'int_part': int(num_abs),
        'frac_part': float('0.' + frac_str) if frac_str else 0.0,
        'terms': terms,
        'frac_terms': [(d, p, v) for d, p, v in terms if p < 0],
        'expression': full,
        'total': total,
        'negative': negative,
    }

def pretty_print_base10_decimal(n: Union[int, float, str]) -> str:
    data = decompose_base10_decimal(n)
    lines: List[str] = []
    lines.append(data['expression'])
    lines.append("Detalle:")
    
    # Filtrar términos que no sean cero para mostrar solo los significativos
    significant_terms = [(d, p, val) for d, p, val in data['terms'] if abs(val) > 1e-10]
    
    for d, p, val in significant_terms:
        lines.append(f"{d} {MULT_SIGN} 10{to_superscript(p)} = {format_number(val)}")

    # Usar solo términos significativos en la suma
    step_sum = " + ".join(format_number(val) for _, _, val in significant_terms)
    lines.append(f"Suma paso a paso: {step_sum} = {format_number(data['total'])}")
    return "\n".join(lines)


# -------------------- BASE 2 --------------------
def _validate_binary_string(value: str) -> str:
    s = value.strip()
    if not s:
        raise ValueError("Entrada binaria vacía")
    if any(ch not in '01' for ch in s):
        raise ValueError("Cadena binaria inválida. Solo '0' y '1' permitidos.")
    return s.lstrip('0') or '0'

def decompose_base2_str(value: str) -> Dict[str, Any]:
    s = _validate_binary_string(value)
    L = len(s)
    bits = list(s)
    terms: List[Tuple[int, int, int]] = []
    total = 0
    for idx, ch in enumerate(bits):
        bit = int(ch)
        power = L - idx - 1
        val = bit * (2 ** power)
        terms.append((bit, power, val))
        total += val

    expr = " + ".join(f"{bit}{MULT_SIGN}2{to_superscript(power)}" for bit, power, _ in terms)
    full = f"{s} = {expr}"
    return {
        'bits': bits,
        'terms': terms,
        'expression': full,
        'total': total,
        'decimal_equiv': total,
        'binary_original': s
    }

def pretty_print_base2_str(value: str) -> str:
    data = decompose_base2_str(value)
    lines: List[str] = []
    lines.append(data['expression'])
    lines.append("Detalle paso a paso:")
    for bit, power, val in data['terms']:
        lines.append(f"{bit} {MULT_SIGN} 2{to_superscript(power)} = {format_number(val)}")
    step_sum = " + ".join(str(format_number(val)) for _, _, val in data['terms'])
    lines.append(f"Suma paso a paso: {step_sum} = {format_number(data['total'])}")

    # Confirmación paso a paso decimal -> binario
    decimal_value = data['total']
    lines.append("Confirmación paso a paso de decimal a binario:")
    if decimal_value == 0:
        lines.append("0 -> binario 0")
    else:
        temp = decimal_value
        bin_manual = ''
        pasos = []
        while temp > 0:
            resto = temp % 2
            pasos.append(f"{temp} ÷ 2 = {temp//2} resto {resto}")
            bin_manual = str(resto) + bin_manual
            temp //= 2
        for paso in pasos:
            lines.append(paso)
        lines.append(f"Binario final: {bin_manual} (original {data['binary_original']})")

    return "\n".join(lines)

# -------------------- INTERFAZ INTERACTIVA --------------------
def _input_prompt(prompt: str) -> str:
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print('\nOperación cancelada por el usuario.')
        return ''

def run_positional_notation_menu() -> None:
    while True:
        print('\n--- NOTACIÓN POSICIONAL ▸ ---')
        print('[1] Descomponer en Base 10')
        print('[2] Descomponer en Base 2')
        print('[0] Volver')
        opt = _input_prompt('Selecciona una opción: ').strip()
        if opt in ('0', 'q', 'salir', ''):
            break
        if opt == '1':
            val = _input_prompt('Ingresa un número (puede ser entero o decimal): ').strip()
            try:
                out = pretty_print_base10_decimal(val)
                print('\n' + out)
            except ValueError as e:
                print(f"Entrada inválida: {e}")
        elif opt == '2':
            val = _input_prompt('Ingresa un número binario (solo 0 y 1): ').strip()
            try:
                out = pretty_print_base2_str(val)
                print('\n' + out)
            except ValueError as e:
                print(f"Entrada inválida: {e}")
        else:
            print('Opción inválida. Intenta de nuevo.')

if __name__ == '__main__':
    run_positional_notation_menu()