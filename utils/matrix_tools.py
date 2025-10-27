# utils/matrix_tools.py
from __future__ import annotations
from typing import List, Tuple
from utils.EquationFunctions import format_number
from utils.printMethods import format_matrix

Matrix = List[List[float]]

# --------------------------
# Validaciones y formas
# --------------------------
def shape_of(M: Matrix) -> Tuple[int, int]:
    return (len(M), len(M[0]) if M else 0)

def same_size(A: Matrix, B: Matrix) -> bool:
    return len(A) == len(B) and (len(A[0]) if A else 0) == (len(B[0]) if B else 0)

def mult_compatible(A: Matrix, B: Matrix) -> bool:
    return (len(A[0]) if A else 0) == len(B)

# --------------------------
# Operaciones básicas (2 operandos)
# --------------------------
def add_matrices(A: Matrix, B: Matrix) -> Tuple[Matrix, str]:
    if not same_size(A, B):
        raise ValueError("Dimensiones incompatibles para suma/resta (mismas filas y columnas).")
    m, n = shape_of(A)
    C = [[A[i][j] + B[i][j] for j in range(n)] for i in range(m)]
    steps = []
    for i in range(m):
        row_terms = []
        for j in range(n):
            row_terms.append(f"({format_number(A[i][j])}) + ({format_number(B[i][j])}) = {format_number(C[i][j])}")
        steps.append(f"  Fila {i+1}: " + " | ".join(row_terms))
    return C, "\n".join(steps)

def sub_matrices(A: Matrix, B: Matrix) -> Tuple[Matrix, str]:
    if not same_size(A, B):
        raise ValueError("Dimensiones incompatibles para suma/resta (mismas filas y columnas).")
    m, n = shape_of(A)
    C = [[A[i][j] - B[i][j] for j in range(n)] for i in range(m)]
    steps = []
    for i in range(m):
        row_terms = []
        for j in range(n):
            row_terms.append(f"({format_number(A[i][j])}) - ({format_number(B[i][j])}) = {format_number(C[i][j])}")
        steps.append(f"  Fila {i+1}: " + " | ".join(row_terms))
    return C, "\n".join(steps)

def scalar_mult(alpha: float, A: Matrix) -> Tuple[Matrix, str]:
    m, n = shape_of(A)
    C = [[alpha * A[i][j] for j in range(n)] for i in range(m)]
    steps = []
    for i in range(m):
        row_terms = []
        for j in range(n):
            row_terms.append(f"{format_number(alpha)}·({format_number(A[i][j])}) = {format_number(C[i][j])}")
        steps.append(f"  Fila {i+1}: " + " | ".join(row_terms))
    return C, "\n".join(steps)

def transpose(A: Matrix) -> Tuple[Matrix, str]:
    m, n = shape_of(A)
    T = [[A[i][j] for i in range(m)] for j in range(n)]
    lines = []
    for j in range(n):
        moved = ", ".join(f"a_{i+1}{j+1}→t_{j+1}{i+1}" for i in range(m))
        lines.append(f"  Columna {j+1} de A pasa a Fila {j+1} de Aᵀ ({moved})")
    return T, "\n".join(lines)

def matmul(A: Matrix, B: Matrix) -> Tuple[Matrix, str]:
    if not mult_compatible(A, B):
        raise ValueError("Dimensiones incompatibles para multiplicación (cols(A) = filas(B)).")
    m, p = len(A), len(B[0])
    n = len(A[0])
    C = [[0.0 for _ in range(p)] for _ in range(m)]
    steps = []
    for i in range(m):
        for j in range(p):
            terms = [f"{format_number(A[i][k])}·{format_number(B[k][j])}" for k in range(n)]
            val = sum(A[i][k]*B[k][j] for k in range(n))
            C[i][j] = val
            steps.append(f"  c_{i+1}{j+1} = " + " + ".join(terms) + f" = {format_number(val)}")
    return C, "\n".join(steps)

# --------------------------
# Operaciones con VARIAS matrices
# --------------------------
def sum_many(mats: List[Matrix]) -> Tuple[Matrix, str]:
    """Suma M1 + M2 + ... + Mk (todas del mismo tamaño)."""
    if len(mats) < 2:
        raise ValueError("Se requieren al menos 2 matrices para la suma.")
    base = mats[0]
    for M in mats[1:]:
        if not same_size(base, M):
            raise ValueError("Todas las matrices deben tener la misma dimensión para sumar.")
    m, n = shape_of(base)
    C = [[0.0 for _ in range(n)] for _ in range(m)]
    steps = []
    for i in range(m):
        for j in range(n):
            terms = [format_number(M[i][j]) for M in mats]
            val = sum(M[i][j] for M in mats)
            C[i][j] = val
            steps.append(f"  s_{i+1}{j+1} = " + " + ".join(terms) + f" = {format_number(val)}")
    return C, "\n".join(steps)

def sub_many(first: Matrix, rest: List[Matrix]) -> Tuple[Matrix, str]:
    """Resta en cadena: M1 - M2 - M3 - ... - Mk (todas del mismo tamaño)."""
    if not rest:
        raise ValueError("Se necesita al menos una matriz para restar a la primera.")
    for M in rest:
        if not same_size(first, M):
            raise ValueError("Todas las matrices deben tener la misma dimensión para restar.")
    mats = [first] + rest
    m, n = shape_of(first)
    C = [[0.0 for _ in range(n)] for _ in range(m)]
    steps = []
    for i in range(m):
        for j in range(n):
            terms = [format_number(first[i][j])] + [f"({format_number(M[i][j])})" for M in rest]
            val = first[i][j] - sum(M[i][j] for M in rest)
            C[i][j] = val
            steps.append(f"  r_{i+1}{j+1} = " + " - ".join(terms) + f" = {format_number(val)}")
    return C, "\n".join(steps)

def matmul_chain(mats: List[Matrix]) -> Tuple[Matrix, str]:
    """Producto en cadena: M1·M2·...·Mk (verifica compatibilidad paso a paso)."""
    if len(mats) < 2:
        raise ValueError("Se requieren al menos 2 matrices para multiplicar.")
    current = mats[0]
    all_steps = []
    for idx, M in enumerate(mats[1:], start=2):
        C, steps = matmul(current, M)
        all_steps.append(f"Paso {idx-1}: resultado anterior · M{idx}\n" + steps)
        current = C
    return current, "\n\n".join(all_steps)

# --------------------------
# Pretty helper
# --------------------------
def pretty_show(title: str, M: Matrix) -> str:
    m, n = shape_of(M)
    return f"{title} ({m}x{n})\n{format_matrix(M)}\n"

# --------------------------
# Propiedades de la traspuesta (solo chequeos que no requieren otra matriz)
# --------------------------
def _equal_matrices(A: Matrix, B: Matrix, tol: float = 1e-12) -> bool:
    if shape_of(A) != shape_of(B):
        return False
    m, n = shape_of(A)
    for i in range(m):
        for j in range(n):
            if abs(A[i][j] - B[i][j]) > tol:
                return False
    return True

def verify_transpose_props(A: Matrix, B: Matrix | None = None) -> str:
    """
    Verifica propiedades típicas de la traspuesta para A (y opcionalmente B):
      • dimensiones de A y A^T
      • (A^T)^T = A
      • (αA)^T = α A^T (probado con α=2)
      • (A+B)^T = A^T + B^T (si B mismo tamaño)
      • (AB)^T = B^T A^T (si cols(A)=filas(B))
    Devuelve un bloque de texto con OK / FALSO o 'No evaluada' si no aplica.
    """
    lines = []
    m, n = shape_of(A)
    AT, _ = transpose(A)
    lines.append(f"Dimensiones: A es {m}x{n} y Aᵀ es {n}x{m}  ->  OK")

    ATT, _ = transpose(AT)
    lines.append("(Aᵀ)ᵀ = A  ->  " + ("OK" if ATT == A else "FALSO"))

    alpha = 2.0
    alphaA, _ = scalar_mult(alpha, A)
    left, _ = transpose(alphaA)
    alphaAT, _ = scalar_mult(alpha, AT)
    lines.append(f"(αA)ᵀ = α·Aᵀ (probado con α = {format_number(alpha)})  ->  "
                 + ("OK" if left == alphaAT else "FALSO"))

    if B is None:
        lines.append("(A + B)ᵀ = Aᵀ + Bᵀ  ->  No evaluada (requiere B del mismo tamaño).")
        lines.append("(A·B)ᵀ = Bᵀ·Aᵀ    ->  No evaluada (requiere B con cols(A)=filas(B)).")
        return "\n".join(lines)

    if same_size(A, B):
        ATpBT, _ = transpose(add_matrices(A, B)[0])
        AT_plus_BT, _ = add_matrices(transpose(A)[0], transpose(B)[0])
        lines.append("(A + B)ᵀ = Aᵀ + Bᵀ  ->  " + ("OK" if ATpBT == AT_plus_BT else "FALSO"))
    else:
        lines.append("(A + B)ᵀ = Aᵀ + Bᵀ  ->  No evaluada (requiere B del mismo tamaño).")

    if mult_compatible(A, B):
        AB, _ = matmul(A, B)
        ABT, _ = transpose(AB)
        BT, _ = transpose(B)
        AT, _ = transpose(A)
        BT_AT, _ = matmul(BT, AT)
        lines.append("(A·B)ᵀ = Bᵀ·Aᵀ    ->  " + ("OK" if ABT == BT_AT else "FALSO"))
    else:
        lines.append("(A·B)ᵀ = Bᵀ·Aᵀ    ->  No evaluada (requiere B con cols(A)=filas(B)).")

    return "\n".join(lines)