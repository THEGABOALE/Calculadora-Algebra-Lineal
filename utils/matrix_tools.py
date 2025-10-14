from __future__ import annotations
from typing import List, Tuple
from utils.EquationFunctions import format_number, parse_fraction
from utils.printMethods import format_matrix

Matrix = List[List[float]]

# --------------------------
# Validaciones y lecturas
# --------------------------
def same_size(A: Matrix, B: Matrix) -> bool:
    return len(A) == len(B) and (len(A[0]) if A else 0) == (len(B[0]) if B else 0)

def mult_compatible(A: Matrix, B: Matrix) -> bool:
    return (len(A[0]) if A else 0) == len(B)

def shape_of(M: Matrix) -> Tuple[int, int]:
    return (len(M), len(M[0]) if M else 0)

# --------------------------
# Operaciones + pasos
# --------------------------
def add_matrices(A: Matrix, B: Matrix) -> Tuple[Matrix, str]:
    """Suma elemento a elemento con pasos."""
    if not same_size(A, B):
        raise ValueError("Dimensiones incompatibles para suma/resta (mismas filas y columnas).")
    m, n = shape_of(A)
    C = [[A[i][j] + B[i][j] for j in range(n)] for i in range(m)]
    steps = []
    for i in range(m):
        row_terms = []
        for j in range(n):
            row_terms.append(f"({format_number(A[i][j])}) + ({format_number(B[i][j])}) = {format_number(C[i][j])}")
        steps.append("  Fila " + str(i+1) + ": " + " | ".join(row_terms))
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
        steps.append("  Fila " + str(i+1) + ": " + " | ".join(row_terms))
    return C, "\n".join(steps)

def scalar_mult(alpha: float, A: Matrix) -> Tuple[Matrix, str]:
    m, n = shape_of(A)
    C = [[alpha * A[i][j] for j in range(n)] for i in range(m)]
    steps = []
    for i in range(m):
        row_terms = []
        for j in range(n):
            row_terms.append(f"{format_number(alpha)}·({format_number(A[i][j])}) = {format_number(C[i][j])}")
        steps.append("  Fila " + str(i+1) + ": " + " | ".join(row_terms))
    return C, "\n".join(steps)

def transpose(A: Matrix) -> Tuple[Matrix, str]:
    m, n = shape_of(A)
    T = [[A[i][j] for i in range(m)] for j in range(n)]
    # Paso didáctico: “intercambio filas↔columnas”
    lines = []
    for j in range(n):
        moved = ", ".join(f"a_{i+1}{j+1}→t_{j+1}{i+1}" for i in range(m))
        lines.append(f"  Columna {j+1} de A pasa a Fila {j+1} de Aᵀ ({moved})")
    return T, "\n".join(lines)

def matmul(A: Matrix, B: Matrix) -> Tuple[Matrix, str]:
    """Producto AB con desarrollo fila·columna explicado para cada entrada."""
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
# Verificaciones útiles
# --------------------------
def verify_transpose_props(A: Matrix) -> str:
    """Verifica propiedades básicas: (Aᵀ)ᵀ = A; (αA)ᵀ = αAᵀ."""
    AT, _ = transpose(A)
    ATT, _ = transpose(AT)
    ok_involution = ATT == [[x for x in row] for row in A]

    alpha = 2.0
    aA, _ = scalar_mult(alpha, A)
    AT2, _ = transpose(aA)
    aAT, _ = scalar_mult(alpha, AT)
    ok_scalar = AT2 == aAT

    msg = []
    msg.append(f"(Aᵀ)ᵀ = A → {'✔' if ok_involution else '✘'}")
    msg.append(f"(αA)ᵀ = αAᵀ con α={format_number(alpha)} → {'✔' if ok_scalar else '✘'}")
    return "\n".join(msg)

def pretty_show(title: str, M: Matrix) -> str:
    return f"{title}\n{format_matrix(M)}\n"
