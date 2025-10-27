# utils/matrix_tools.py
from __future__ import annotations
from typing import List, Tuple
from utils.EquationFunctions import format_number
from utils.printMethods import format_matrix
from utils.printMethods import log_step

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
# Helpers: rank, RREF, nullspace, mult
# --------------------------
def _copy_matrix(A: Matrix) -> Matrix:
    return [row[:] for row in A]

def multiply_mat_vec(A: Matrix, v: List[float]) -> List[float]:
    m, n = shape_of(A)
    if len(v) != n:
        raise ValueError("Dimensiones incompatibles para multiplicar matriz por vector.")
    return [sum(A[i][j] * v[j] for j in range(n)) for i in range(m)]

def _rref_matrix(A: Matrix, tol: float = 1e-12) -> Tuple[Matrix, int]:
    """Devuelve una copia en RREF y el rango (número de pivotes no nulos)."""
    M = _copy_matrix(A)
    m, n = shape_of(M)
    row = 0
    pivots = 0
    for col in range(n):
        if row >= m:
            break
        # buscar pivote en [row..m-1]
        sel = row
        best = abs(M[row][col])
        for r in range(row + 1, m):
            v = abs(M[r][col])
            if v > best:
                best = v
                sel = r
        if best <= tol:
            continue
        if sel != row:
            M[row], M[sel] = M[sel], M[row]
        pivot = M[row][col]
        # escalar fila
        for j in range(col, n):
            M[row][j] = M[row][j] / pivot
        # anular otras filas
        for r in range(m):
            if r == row:
                continue
            factor = M[r][col]
            if abs(factor) <= tol:
                continue
            for j in range(col, n):
                M[r][j] = M[r][j] - factor * M[row][j]
        row += 1
        pivots += 1
    return M, pivots

def rank_of(A: Matrix, tol: float = 1e-12) -> int:
    _, pivots = _rref_matrix(A, tol=tol)
    return pivots

def nullspace_vector(A: Matrix, tol: float = 1e-12) -> List[float] | None:
    """Intenta construir un vector no trivial x tal que A x = 0 si existe.
    Devuelve None si sólo la solución trivial.
    Regresa un vector con una libre asignada a 1 cuando sea posible.
    """
    m, n = shape_of(A)
    # Construir matriz aumentada [A | 0]
    M = [row[:] + [0.0] for row in _copy_matrix(A)]
    R, pivots = _rref_matrix(M, tol=tol)
    if pivots == n:
        return None
    # identificar columnas pivote
    pivot_cols = []
    for i in range(m):
        for j in range(n):
            if abs(R[i][j]) > tol:
                pivot_cols.append(j)
                break
    pivot_set = set(pivot_cols)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if not free_cols:
        return None
    free = free_cols[0]
    x = [0.0] * n
    x[free] = 1.0
    # para cada pivote, resolver el valor en función de variables libres
    # recorrer filas y encontrar la ecuación con pivot en columna p
    for i in range(m):
        # buscar pivot en la fila
        pcol = None
        for j in range(n):
            if abs(R[i][j]) > tol:
                pcol = j
                break
        if pcol is None:
            continue
        # suma de R[i][pcol]*x[pcol] + sum_{free} R[i][f]*x[f] = 0
        s = 0.0
        for f in free_cols:
            s += R[i][f] * x[f]
        # como R está en RREF, R[i][pcol] debería ser 1
        x[pcol] = -s
    return x

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


def verify_inverse_props(A: Matrix, B: Matrix | None = None, tol: float = 1e-12) -> str:
    """Verifica propiedades relacionadas con inversas:
      a) (A^{-1})^{-1} = A
      b) Si B dado: (AB)^{-1} = B^{-1} A^{-1} (cuando aplicable)
      c) (A^T)^{-1} = (A^{-1})^T
    Devuelve un bloque de texto con OK / FALSO / No evaluada.
    """
    lines: List[str] = []
    m, n = shape_of(A)
    if m != n:
        return "No evaluada: A no es cuadrada."

    # calcular inversa de A si es posible
    try:
        Ainv, _ = inverse(A, tol=tol, check_props=False)
    except Exception as e:
        return f"No evaluada: A no invertible ({e})."

    # a) (A^{-1})^{-1} = A
    try:
        Ainvinv, _ = inverse(Ainv, tol=tol, check_props=False)
        ok_a = _equal_matrices(Ainvinv, A, tol=tol)
        lines.append("a) (A^{-1})^{-1} = A  ->  " + ("OK" if ok_a else "FALSO"))
    except Exception:
        lines.append("a) (A^{-1})^{-1} = A  ->  No evaluada (no fue posible invertir A^{-1}).")

    # b) (AB)^{-1} = B^{-1} A^{-1}
    if B is None:
        lines.append("b) (AB)^{-1} = B^{-1}·A^{-1}  ->  No evaluada (requiere B).")
    else:
        if not mult_compatible(A, B):
            lines.append("b) (AB)^{-1} = B^{-1}·A^{-1}  ->  No evaluada (incompatibilidad: cols(A) != filas(B)).")
        else:
            # intentar invertir AB y B
            try:
                AB, _ = matmul(A, B)
                ABinv, _ = inverse(AB, tol=tol, check_props=False)
                Binv, _ = inverse(B, tol=tol, check_props=False)
                RHS, _ = matmul(Binv, Ainv)
                ok_b = _equal_matrices(ABinv, RHS, tol=tol)
                lines.append("b) (AB)^{-1} = B^{-1}·A^{-1}  ->  " + ("OK" if ok_b else "FALSO"))
            except Exception as e:
                lines.append(f"b) (AB)^{-1} = B^{-1}·A^{-1}  ->  No evaluada ({e}).")

    # c) (A^T)^{-1} = (A^{-1})^T
    try:
        AT, _ = transpose(A)
        ATinv, _ = inverse(AT, tol=tol, check_props=False)
        AinvT, _ = transpose(Ainv)
        ok_c = _equal_matrices(ATinv, AinvT, tol=tol)
        lines.append("c) (A^T)^{-1} = (A^{-1})^T  ->  " + ("OK" if ok_c else "FALSO"))
    except Exception as e:
        lines.append(f"c) (A^T)^{-1} = (A^{-1})^T  ->  No evaluada ({e}).")

    return "\n".join(lines)


# --------------------------
# Determinante / Inversa (usando Gauss-Jordan)
# --------------------------
def determinant(A: Matrix, tol: float = 1e-12) -> float:
    """
    Calcula el determinante de A usando una reducción tipo Gauss-Jordan
    con pivoteo parcial por filas. Se siguen operaciones elementales y
    se acumula el producto de los pivotes antes de normalizar (escala).
    Devuelve 0.0 si la matriz es singular.
    """
    # Verificar cuadrada
    m, n = shape_of(A)
    if m != n:
        raise ValueError("Determinante sólo definido para matrices cuadradas.")

    # Hacer copia para no modificar A
    M = [row[:] for row in A]
    det = 1.0
    row = 0
    swaps = 0
    for col in range(n):
        if row >= n:
            break
        # seleccionar fila con mayor valor absoluto en columna `col`
        sel = row
        best = abs(M[row][col])
        for r in range(row + 1, n):
            v = abs(M[r][col])
            if v > best:
                best = v
                sel = r

        if best <= tol:
            # columna sin pivote significativo -> determinante 0
            return 0.0

        if sel != row:
            M[row], M[sel] = M[sel], M[row]
            swaps += 1

        pivot = M[row][col]
        # acumular el valor del pivote (antes de escalar a 1)
        det *= pivot

        # escalar la fila para dejar 1 en la posición pivote (como en Gauss-Jordan)
        for j in range(col, n):
            M[row][j] = M[row][j] / pivot

        # eliminación: hacer ceros en todas las demás filas (arriba y abajo)
        for r in range(n):
            if r == row:
                continue
            factor = M[r][col]
            if abs(factor) <= tol:
                continue
            for j in range(col, n):
                M[r][j] = M[r][j] - factor * M[row][j]

        row += 1

    if swaps % 2 != 0:
        det = -det
    return 0.0 if abs(det) <= tol else det


def is_singular(A: Matrix, tol: float = 1e-12) -> bool | None:
    """Devuelve True si A cuadrada y singular, False si no singular, None si no es cuadrada."""
    m, n = shape_of(A)
    if m != n:
        return None
    try:
        d = determinant(A, tol=tol)
    except ValueError:
        return None
    return abs(d) <= tol


def inverse(A: Matrix, tol: float = 1e-12, frame: dict | None = None, b: List[float] | None = None, check_props: bool = True) -> Tuple[Matrix, str]:
    """
    Calcula la inversa de A usando Gauss-Jordan sobre [A | I].
    Si se proporciona `frame` (dict), la función registrará cada paso
    (matriz aumentada y operaciones) usando `log_step` para que luego
    pueda imprimirse con `print_frame` con el mismo estilo que el resto
    de los métodos.

    Retorna (A_inv, steps_text) donde steps_text incluye el listado de
    operaciones elementales y, además, la matriz de cofactores, la adjunta
    y la inversa obtenida por Adj(A)/det(A) cuando corresponde.
    """
    m, n = shape_of(A)
    if m != n:
        raise ValueError("La inversa sólo está definida para matrices cuadradas.")

    # Si se pide, comprobar propiedades relacionadas con sistemas Ax = b o Ax = 0
    if b is not None and len(b) != m:
        raise ValueError("Dimensión de b incompatible con A para Ax=b.")

    # Comprobar singularidad antes de proceder: si es singular lanzar error pero
    # proporcionando información pedagógica (determinante, rango, existencia de núcleo no trivial).
    detA = determinant(A, tol=tol)
    if abs(detA) <= tol:
        # preparar texto explicativo antes de lanzar para mantener comportamiento de tests (excepción)
        rA = rank_of(A, tol=tol)
        detailed = []
        detailed.append(f"Matriz singular: det(A) = {format_number(detA)} (≈ 0)")
        detailed.append(f"Rango de A = {rA} (< {n} si singular)")
        detailed.append("Consecuencias:")
        detailed.append(" - No existe A^{-1}.")
        detailed.append(" - Las columnas de A son linealmente dependientes; núcleo no trivial existe.")
        nullv = nullspace_vector(A, tol=tol)
        if nullv is not None:
            detailed.append(" - Ejemplo de vector no trivial en Núcleo (Ax=0):")
            detailed.append(format_matrix([nullv]))
        # Si el usuario preguntó por un b, analizar consistencia del sistema Ax=b
        if b is not None:
            # construir matriz aumentada y comparar rangos
            Aug = [row[:] + [bv] for row, bv in zip(A, b)]
            rAug = rank_of(Aug, tol=tol)
            if rAug > rA:
                detailed.append(f"Sistema Ax=b inconsistente: rango([A|b]) = {rAug} > rango(A) = {rA} -> Sin soluciones.")
            else:
                detailed.append(f"Sistema Ax=b consistente y tiene infinitas soluciones (rango = {rA} < {n}).")
        detailed_text = "\n".join(detailed)
        raise ValueError(detailed_text)

    # Copia y matriz aumentada [A | I]
    M = [list(map(float, row)) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate([r[:] for r in A])]
    steps_list: List[str] = []
    # registrar estado inicial en frame si se proporcionó
    if frame is not None:
        log_step(frame, "Matriz aumentada inicial [A | I]", M, det=None, tag="inverse_start")

    row = 0
    for col in range(n):
        if row >= n:
            break
        # seleccionar fila con mayor valor absoluto en columna `col`
        sel = row
        best = abs(M[row][col])
        for r in range(row + 1, n):
            v = abs(M[r][col])
            if v > best:
                best = v
                sel = r

        if best <= tol:
            # columna sin pivote significativo -> matriz singular
            raise ValueError("Matriz singular (no tiene pivote en la columna {})".format(col+1))

        if sel != row:
            M[row], M[sel] = M[sel], M[row]
            steps_list.append(f"F{row+1} <-> F{sel+1}")
            if frame is not None:
                log_step(frame, f"F{row+1} <-> F{sel+1}", M, det=None, tag="swap_rows")

        pivot = M[row][col]
        # Escalar para hacer 1 el pivote
        if abs(pivot - 1.0) > tol:
            for j in range(col, 2*n):
                M[row][j] = M[row][j] / pivot
            steps_list.append(f"F{row+1} -> F{row+1} / {format_number(pivot)}")
            if frame is not None:
                log_step(frame, f"F{row+1} -> F{row+1} / {format_number(pivot)}", M, det=None, tag="scale")

        # eliminación: hacer ceros en todas las demás filas (arriba y abajo)
        for r in range(n):
            if r == row:
                continue
            factor = M[r][col]
            if abs(factor) <= tol:
                continue
            for j in range(col, 2*n):
                M[r][j] = M[r][j] - factor * M[row][j]
            signo = "-" if factor > 0 else "+"
            steps_list.append(f"F{r+1} -> F{r+1} {signo} {format_number(abs(factor))}*F{row+1}")
            if frame is not None:
                log_step(frame, f"F{r+1} -> F{r+1} {signo} {format_number(abs(factor))}*F{row+1}", M, det=None, tag="elim")

        row += 1

    # Extraer la parte derecha como inversa
    Ainv = [[M[i][j] for j in range(n, 2*n)] for i in range(n)]
    if frame is not None:
        log_step(frame, "Forma reducida por filas (RREF) sobre [A | I] -> [I | A⁻¹]", M, det=None, tag="rref")
        log_step(frame, "Matriz inversa (A⁻¹)", Ainv, det=None, tag="inverse_result")

    # Preparar texto detallado con operaciones y derivadas pedagógicas (cofactores / adjunta)
    detailed_lines: List[str] = []
    detailed_lines.append("Pasos (operaciones elementales - Gauss-Jordan sobre [A | I]):")
    detailed_lines.extend(steps_list)

    # Matriz de cofactores y adjunta (útil pedagógicamente para tamaños pequeños)
    def _minor_matrix(B: Matrix, ii: int, jj: int) -> Matrix:
        return [[B[r][c] for c in range(len(B)) if c != jj] for r in range(len(B)) if r != ii]

    cofactors = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            minor = _minor_matrix(A, i, j)
            det_minor = determinant(minor) if minor else 1.0
            cofactors[i][j] = ((-1) ** (i + j)) * det_minor

    adjugate = [[cofactors[j][i] for j in range(n)] for i in range(n)]

    detailed_lines.append("\nMatriz de cofactores (C):")
    detailed_lines.append(format_matrix(cofactors))
    if frame is not None:
        log_step(frame, "Matriz de cofactores (C)", cofactors, det=None, tag="cofactors")

    detailed_lines.append("\nMatriz adjunta (Adj(A) = C^T):")
    detailed_lines.append(format_matrix(adjugate))
    if frame is not None:
        log_step(frame, "Matriz adjunta (Adj(A) = C^T)", adjugate, det=None, tag="adjugate")

    try:
        detA = determinant(A)
        detailed_lines.append(f"\nDeterminante de A = {format_number(detA)}")
        if frame is not None:
            log_step(frame, f"Determinante de A = {format_number(detA)}", A, det=detA, tag="det")
        if abs(detA) > tol:
            detailed_lines.append("\nMatriz inversa = (1/det(A)) * Adj(A)")
            inv_by_adj = [[adjugate[i][j] / detA for j in range(n)] for i in range(n)]
            detailed_lines.append("\nAdj(A) / det(A):")
            detailed_lines.append(format_matrix(inv_by_adj))
    except Exception:
        pass

    detailed_lines.append("\nResultado final (A⁻¹):")
    detailed_lines.append(format_matrix(Ainv))

    # Si se proporcionó un vector b, comprobar que x = A⁻¹ b satisface Ax = b
    if b is not None:
        try:
            x = multiply_mat_vec(Ainv, b)
            Ax = multiply_mat_vec(A, x)
            detailed_lines.append("\nVerificación de Ax = b usando A⁻¹:")
            detailed_lines.append(f"x = A⁻¹·b = {format_matrix([x])}")
            detailed_lines.append(f"A·x = {format_matrix([Ax])}")
            ok = all(abs(Ax[i] - b[i]) <= 1e-9 for i in range(len(b)))
            detailed_lines.append("Verificación: " + ("OK (Ax ≈ b)" if ok else "FALSO (Ax != b)"))
        except Exception as e:
            detailed_lines.append(f"Error verificando Ax=b: {e}")

    # Añadir recordatorio de teoremas útiles (con comprobaciones automáticas)
    detailed_lines.append("\nPropiedades útiles (teorema) - comprobaciones:")
    if check_props:
        try:
            inv_checks = verify_inverse_props(A, None, tol=tol)
            detailed_lines.append(inv_checks)
        except Exception as e:
            detailed_lines.append(f"No fue posible evaluar propiedades de inversa: {e}")
    else:
        detailed_lines.append("(Comprobaciones de propiedades deshabilitadas para evitar recursión interna.)")

    return Ainv, "\n".join(detailed_lines)