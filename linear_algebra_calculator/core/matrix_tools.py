# utils/matrix_tools.py
from __future__ import annotations
import math
import sys
import warnings
from typing import List, Optional, Tuple
from utils.EquationFunctions import format_number
from utils.printMethods import format_matrix
from utils.printMethods import log_step

Matrix = List[List[float]]

# --------------------------
# Criterio numérico de "cero" (compartido por rango, determinante,
# singularidad, inversa y la clasificación de Cramer)
# --------------------------
# En coma flotante casi ningún resultado de una eliminación da 0 exacto, así
# que hace falta decidir cuándo un número es "cero". Un umbral ABSOLUTO (el
# 1e-12 que se usaba antes) depende de la escala: declara singular a
# 1e-5·I (det = 1e-15) y, al revés, deja pasar ruido en matrices grandes. Un
# umbral relativo al máximo de toda la matriz tampoco alcanza: con
# diag(1e8, 1e-8), o con [A|b] cuando b tiene otra magnitud que A, la columna
# chica quedaría por debajo del umbral de la grande.
#
# Criterio elegido: COTA DE REDONDEO POR ENTRADA. Junto a cada entrada M[i][j]
# se lleva S[i][j], la suma de los valores absolutos que intervinieron en
# calcularla (al inicio S = |M|; en cada M[r] -= f·M[p], S[r] += |f|·S[p]).
# El error de redondeo acumulado en M[i][j] es del orden de eps·S[i][j], así
# que una entrada se considera cero si
#
#     |M[i][j]| <= tau · S[i][j],    tau = FACTOR · max(m, n) · eps
#
# Propiedades: un dato que es 0 exacto sigue siendo 0 (S = 0); una entrada
# que no participó en ninguna operación nunca se declara cero, por chica que
# sea; escalar filas o columnas de la entrada no cambia la decisión; y cada
# columna -- incluida la de b en [A|b] -- se juzga con sus propias
# magnitudes, sin normalizar nada.
#
# FACTOR = 1e4 es una calibración empírica, no un teorema: los decimales que
# tipea un usuario (0.1, 0.3...) no son representables en binario, así que
# una matriz singular "como se escribió" llega levemente no singular. Sobre
# 20.000 matrices singulares con entradas decimales de 1-2 cifras el ruido
# medido llegó a ~2.5e3 en unidades de max(m,n)·eps·S; los pivotes legítimos
# quedaron por encima de 5e10. Consecuencia documentada: una matriz cuya
# singularidad se decide recién en la ~12ª cifra significativa (número de
# condición del orden de 1e12 o mayor) se trata como numéricamente singular.
#
# Si el llamador pasa un `tol` explícito, se respeta como umbral absoluto
# (comportamiento anterior), para no romper a quien lo use a propósito.
_EPS = sys.float_info.epsilon
FACTOR_REDONDEO = 1e4


def _tau(m: int, n: int) -> float:
    return FACTOR_REDONDEO * max(m, n, 1) * _EPS


def _es_cero(valor: float, cota: float, tau: float, tol: Optional[float]) -> bool:
    if tol is not None:
        return abs(valor) <= tol
    return abs(valor) <= tau * cota


def producto_sin_desborde(factores, signo: float = 1.0) -> float:
    """Producto de `factores` (por `signo`) sin subdesborde ni desborde
    INTERMEDIOS.

    Multiplicar de a uno pierde el resultado aunque sea representable:
    1e-200 · 1e-200 · 1e300 da 0.0 (el parcial 1e-400 subdesborda) y
    1e200 · 1e200 · 1e-300 da inf, cuando el producto es 1e-100 / 1e100. Acá
    se acumula mantisa y exponente por separado (math.frexp) y el número se
    arma una sola vez al final, así que sólo se pierde si el RESULTADO no
    entra en un double: 0.0 si subdesborda, ±inf si desborda.

    Para números normales el resultado es idéntico al de multiplicar de a
    uno: escalar por una potencia de 2 es exacto, así que cada producto de
    mantisas redondea igual que el producto original.
    """
    mantisa, exponente = float(signo), 0
    for factor in factores:
        if factor == 0:
            return 0.0
        m_f, e_f = math.frexp(factor)
        mantisa, e_norm = math.frexp(mantisa * m_f)
        exponente += e_f + e_norm
    try:
        return math.ldexp(mantisa, exponente)
    except OverflowError:
        return math.copysign(math.inf, mantisa)


class CotasDeRedondeo:
    """El criterio de cero de este módulo, para métodos que hacen su propia
    eliminación paso a paso (Gauss, Gauss-Jordan).

    No ejecuta ninguna operación sobre la matriz: el método hace y registra
    las suyas (cada uno con su procedimiento) y le avisa a esta clase cada
    operación elemental, para que lleve la cota S en paralelo:

        cotas = CotasDeRedondeo(M)
        ... M[r], M[p] = M[p], M[r];     cotas.intercambiar(r, p)
        ... M[r] = M[r] / f;             cotas.escalar(r, f)
        ... M[r] = M[r] - f·M[p];        cotas.restar(r, p, f)
        ... if cotas.es_cero(M[i][j], i, j): M[i][j] = 0.0

    Así "es cero" se decide igual que en rank_of / determinant / inverse /
    system_ranks, y la eliminación deja el ruido en 0.0 EXACTO: el análisis
    posterior (analyze_argumented, solve_from_upper) sólo lee ceros exactos.
    """

    def __init__(self, M: Matrix, tol: Optional[float] = None) -> None:
        self.S: Matrix = [[abs(float(x)) for x in fila] for fila in M]
        m = len(M)
        n = len(M[0]) if M else 0
        self.tau = _tau(m, n)
        self.tol = tol

    def es_cero(self, valor: float, i: int, j: int) -> bool:
        return _es_cero(valor, self.S[i][j], self.tau, self.tol)

    def intercambiar(self, i: int, k: int) -> None:
        self.S[i], self.S[k] = self.S[k], self.S[i]

    def escalar(self, i: int, factor: float, desde: int = 0) -> None:
        """Fila i dividida por `factor`."""
        a = abs(factor)
        for j in range(desde, len(self.S[i])):
            self.S[i][j] = self.S[i][j] / a

    def restar(self, destino: int, origen: int, factor: float, desde: int = 0) -> None:
        """Fila destino menos `factor` veces la fila origen."""
        a = abs(factor)
        for j in range(desde, len(self.S[destino])):
            self.S[destino][j] = self.S[destino][j] + a * self.S[origen][j]

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

def _reducir(A: Matrix, tol: Optional[float] = None) -> Tuple[Matrix, List[int], float]:
    """Gauss-Jordan con pivoteo parcial y el criterio de cero de arriba.

    Devuelve (R, columnas_pivote, producto_de_pivotes):
    - R: copia de A en RREF; las entradas que el criterio declara cero
      quedan en 0.0 exacto (ruido de redondeo, no dato).
    - columnas_pivote: en orden de fila; su largo es el rango.
    - producto_de_pivotes: producto de los pivotes ANTES de normalizarlos,
      con el signo de los intercambios. Si A es cuadrada y de rango completo
      es det(A); si no, no significa nada y quien lo use debe mirar el rango.
      Se acumula con producto_sin_desborde (mantisa y exponente, armado
      recién al final): multiplicar de a uno subdesbordaba con diag(1e-200, 1e-200,
      1e300) aunque det = 1e-100 es representable. Si el producto FINAL no
      es representable, queda 0.0 (subdesborda) o ±inf (desborda).

    Es la única eliminación detrás de rank_of, determinant e is_singular, así
    que los tres no pueden discrepar sobre qué columnas tienen pivote (es
    decir, sobre la singularidad). El VALOR del determinante es otra cosa:
    puede no ser representable aunque haya n pivotes (ver determinant).
    """
    M = [[float(x) for x in row] for row in A]
    m, n = shape_of(M)
    S = [[abs(x) for x in row] for row in M]
    tau = _tau(m, n)
    pivot_cols: List[int] = []
    pivotes: List[float] = []
    signo = 1.0
    row = 0
    for col in range(n):
        if row >= m:
            break
        candidatos = [r for r in range(row, m) if not _es_cero(M[r][col], S[r][col], tau, tol)]
        if not candidatos:
            # Columna sin pivote: lo que quede debajo es ruido -> 0 exacto.
            for r in range(row, m):
                M[r][col] = 0.0
            continue
        sel = max(candidatos, key=lambda r: abs(M[r][col]))
        if sel != row:
            M[row], M[sel] = M[sel], M[row]
            S[row], S[sel] = S[sel], S[row]
            signo = -signo
        pivot = M[row][col]
        pivotes.append(pivot)
        # escalar fila (la cota relativa se escala igual)
        for j in range(col, n):
            M[row][j] = M[row][j] / pivot
            S[row][j] = S[row][j] / abs(pivot)
        M[row][col] = 1.0
        # anular la columna en las demás filas
        for r in range(m):
            if r == row:
                continue
            factor = M[r][col]
            if factor == 0.0:
                continue
            for j in range(col + 1, n):
                M[r][j] = M[r][j] - factor * M[row][j]
                S[r][j] = S[r][j] + abs(factor) * S[row][j]
                if _es_cero(M[r][j], S[r][j], tau, tol):
                    M[r][j] = 0.0
            M[r][col] = 0.0
        pivot_cols.append(col)
        row += 1
    return M, pivot_cols, producto_sin_desborde(pivotes, signo)

def _rref_matrix(A: Matrix, tol: Optional[float] = None) -> Tuple[Matrix, int]:
    """Devuelve una copia en RREF y el rango (número de pivotes no nulos)."""
    R, pivot_cols, _ = _reducir(A, tol=tol)
    return R, len(pivot_cols)

def rank_of(A: Matrix, tol: Optional[float] = None) -> int:
    return len(_reducir(A, tol=tol)[1])

def system_ranks(A: Matrix, b: List[float], tol: Optional[float] = None) -> Tuple[int, int]:
    """(rango(A), rango([A|b])) para el teorema de Rouché–Frobenius.

    Sale de UNA sola eliminación sobre [A|b]: las columnas se procesan de
    izquierda a derecha y la elección de pivote en una columna de A no mira
    la de b, así que el rango de A que resulta es exactamente el que daría
    rank_of(A). Por construcción rango([A|b]) - rango(A) es 0 o 1. No se
    normaliza nada: la columna b se juzga con sus propias magnitudes.
    """
    m, n = shape_of(A)
    if len(b) != m:
        raise ValueError("El vector b debe tener tantas entradas como filas tiene A.")
    aumentada = [list(row) + [bi] for row, bi in zip(A, b)]
    pivot_cols = _reducir(aumentada, tol=tol)[1]
    rango_a = sum(1 for c in pivot_cols if c < n)
    return rango_a, len(pivot_cols)

def nullspace_vector(A: Matrix, tol: Optional[float] = None) -> List[float] | None:
    """Intenta construir un vector no trivial x tal que A x = 0 si existe.
    Devuelve None si sólo la solución trivial.
    Regresa un vector con una libre asignada a 1 cuando sea posible.
    """
    m, n = shape_of(A)
    R, pivot_cols, _ = _reducir(A, tol=tol)
    pivot_set = set(pivot_cols)
    free_cols = [j for j in range(n) if j not in pivot_set]
    if not free_cols:
        return None
    free = free_cols[0]
    x = [0.0] * n
    x[free] = 1.0
    # Fila i de R tiene su pivote (= 1) en pivot_cols[i]:
    # x[p] + sum_{libres} R[i][f]*x[f] = 0
    for i, pcol in enumerate(pivot_cols):
        s = 0.0
        for f in free_cols:
            s += R[i][f] * x[f]
        x[pcol] = -s
    return x

# --------------------------
# Propiedades de la traspuesta (solo chequeos que no requieren otra matriz)
# --------------------------
def _equal_matrices(A: Matrix, B: Matrix, tol: Optional[float] = None) -> bool:
    """Igualdad entrada a entrada.

    Sin `tol`, la tolerancia es RELATIVA a la mayor magnitud de las dos
    matrices (1e-9 de esa escala). Con el 1e-12 absoluto de antes, una
    inversa válida de 1e-5·I (entradas 1e5) fallaba (A⁻¹)⁻¹ = A por puro
    redondeo. 1e-9 deja margen para número de condición ~1e6; por encima,
    una propiedad verdadera puede salir FALSO por pérdida de precisión.
    """
    if shape_of(A) != shape_of(B):
        return False
    m, n = shape_of(A)
    if tol is None:
        escala = max([abs(x) for row in A for x in row] + [abs(x) for row in B for x in row] + [0.0])
        tol = 1e-9 * escala
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


def verify_inverse_props(A: Matrix, B: Matrix | None = None, tol: Optional[float] = None) -> str:
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
def determinant(A: Matrix, tol: Optional[float] = None) -> float:
    """
    Calcula el determinante de A usando una reducción tipo Gauss-Jordan
    con pivoteo parcial por filas: producto de los pivotes antes de
    normalizarlos, con el signo de los intercambios.

    Usa la misma eliminación que rank_of, y NO compara el resultado final
    contra ningún umbral: el tamaño de det(A) no mide singularidad
    (det(c·I) = cⁿ), y antes eso devolvía 0 para 1e-5·I. Casos:

    - rango(A) < n (numéricamente singular)  -> 0.0 exacto.
    - rango(A) = n y det representable        -> el producto de los pivotes,
      por chico o grande que sea (1e-15, 1e-100...).
    - rango(A) = n y det NO representable en un double (|det| fuera de
      ~[5e-324, 1.8e308]; p. ej. 1e-110·I₃ da 1e-330) -> 0.0 por
      subdesbordamiento o ±inf por desbordamiento, y un RuntimeWarning.

    Por eso "determinant(A) == 0.0" NO equivale a "A es singular": implica
    singular sólo si el valor es representable. Para decidir singularidad
    se usa is_singular(A) / rank_of(A), que no dependen del rango de
    exponentes de la coma flotante. Se mantiene el tipo de retorno (float)
    para no cambiar el contrato con quienes ya llaman a esta función.
    """
    # Verificar cuadrada
    m, n = shape_of(A)
    if m != n:
        raise ValueError("Determinante sólo definido para matrices cuadradas.")
    _, pivot_cols, producto = _reducir(A, tol=tol)
    if len(pivot_cols) < n:
        return 0.0
    if producto == 0.0 or math.isinf(producto):
        warnings.warn(
            "A es invertible (rango completo) pero det(A) no es representable en coma "
            f"flotante: se devuelve {producto} por {'subdesbordamiento' if producto == 0.0 else 'desbordamiento'}. "
            "Para decidir singularidad usá is_singular(A) o rank_of(A).",
            RuntimeWarning, stacklevel=2,
        )
    return producto


def is_singular(A: Matrix, tol: Optional[float] = None) -> bool | None:
    """Devuelve True si A cuadrada y singular, False si no singular, None si no es cuadrada.

    Singular <=> rango(A) < n, con el mismo criterio de pivotes que
    rank_of y determinant. Es la función a usar para decidir singularidad:
    determinant(A) puede valer 0.0 en una matriz invertible si |det(A)|
    subdesborda (no es representable en un double).
    """
    m, n = shape_of(A)
    if m != n:
        return None
    return rank_of(A, tol=tol) < n


def inverse(A: Matrix, tol: Optional[float] = None, frame: list | None = None, b: List[float] | None = None, check_props: bool = True) -> Tuple[Matrix, str]:
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
    # Mismo criterio que rank_of/determinant/is_singular: singular <=> rango < n.
    rA = rank_of(A, tol=tol)
    if rA < n:
        # preparar texto explicativo antes de lanzar para mantener comportamiento de tests (excepción)
        detA = determinant(A, tol=tol)
        detailed = []
        detailed.append(f"Matriz singular: det(A) = {format_number(detA)} (numéricamente 0: rango de A < n)")
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
            # comparar rangos (Rouché–Frobenius) sobre [A|b], sin normalizar b
            _, rAug = system_ranks(A, b, tol=tol)
            if rAug > rA:
                detailed.append(f"Sistema Ax=b inconsistente: rango([A|b]) = {rAug} > rango(A) = {rA} -> Sin soluciones.")
            else:
                detailed.append(f"Sistema Ax=b consistente y tiene infinitas soluciones (rango = {rA} < {n}).")
        detailed_text = "\n".join(detailed)
        raise ValueError(detailed_text)

    # Copia y matriz aumentada [A | I]
    M = [list(map(float, row)) + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate([r[:] for r in A])]
    # Cota de redondeo por entrada (ver el criterio al principio del módulo).
    S = [[abs(x) for x in row] for row in M]
    tau = _tau(n, 2 * n)
    steps_list: List[str] = []
    # registrar estado inicial en frame si se proporcionó
    if frame is not None:
        log_step(frame, "Matriz aumentada inicial [A | I]", M, det=None, tag="inverse_start")

    row = 0
    for col in range(n):
        if row >= n:
            break
        # seleccionar, entre las entradas que no son cero según el criterio,
        # la de mayor valor absoluto en la columna `col`
        candidatos = [r for r in range(row, n) if not _es_cero(M[r][col], S[r][col], tau, tol)]
        if not candidatos:
            # columna sin pivote significativo -> matriz singular. No debería
            # pasar: el chequeo de rango de arriba usa la misma eliminación.
            raise ValueError("Matriz singular (no tiene pivote en la columna {})".format(col+1))
        sel = max(candidatos, key=lambda r: abs(M[r][col]))

        if sel != row:
            M[row], M[sel] = M[sel], M[row]
            S[row], S[sel] = S[sel], S[row]
            steps_list.append(f"F{row+1} <-> F{sel+1}")
            if frame is not None:
                log_step(frame, f"F{row+1} <-> F{sel+1}", M, det=None, tag="swap_rows")

        pivot = M[row][col]
        # Escalar para hacer 1 el pivote. Antes se salteaba si |pivote-1| <=
        # 1e-12, dejando un pivote que no era 1; ahora sólo si es 1 exacto.
        if pivot != 1.0:
            for j in range(col, 2*n):
                M[row][j] = M[row][j] / pivot
                S[row][j] = S[row][j] / abs(pivot)
            M[row][col] = 1.0
            steps_list.append(f"F{row+1} -> F{row+1} / {format_number(pivot)}")
            if frame is not None:
                log_step(frame, f"F{row+1} -> F{row+1} / {format_number(pivot)}", M, det=None, tag="scale")

        # eliminación: hacer ceros en todas las demás filas (arriba y abajo)
        for r in range(n):
            if r == row:
                continue
            factor = M[r][col]
            # Antes: `abs(factor) <= 1e-12 -> continue`, que en una matriz de
            # entradas ~1e-13 se salteaba eliminaciones reales. Ahora sólo se
            # saltea un factor que el criterio declara ruido.
            if _es_cero(factor, S[r][col], tau, tol):
                M[r][col] = 0.0
                continue
            for j in range(col, 2*n):
                M[r][j] = M[r][j] - factor * M[row][j]
                S[r][j] = S[r][j] + abs(factor) * S[row][j]
                if _es_cero(M[r][j], S[r][j], tau, tol):
                    M[r][j] = 0.0
            M[r][col] = 0.0
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
    # Llegar acá implica rango completo. Si algún determinante (de A o de un
    # menor) no es representable en coma flotante, determinant() avisa con
    # RuntimeWarning; acá se captura y se dice en el texto, en vez de
    # mostrar "det(A) = 0" de una matriz invertible.
    with warnings.catch_warnings(record=True) as avisos_cofactores:
        warnings.simplefilter("always", RuntimeWarning)
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            detA = determinant(A)
        if detA == 0.0 or math.isinf(detA):
            # rango completo (si no, se habría lanzado arriba): no es singular,
            # es que |det(A)| no entra en un double.
            texto_det = ("Determinante de A: no representable en coma flotante "
                         f"({'subdesborda a 0' if detA == 0.0 else 'desborda a infinito'}); "
                         "A es invertible (rango completo)")
            detailed_lines.append("\n" + texto_det)
            if frame is not None:
                log_step(frame, texto_det, A, det=None, tag="det")
        else:
            detailed_lines.append(f"\nDeterminante de A = {format_number(detA)}")
            if frame is not None:
                log_step(frame, f"Determinante de A = {format_number(detA)}", A, det=detA, tag="det")
        if avisos_cofactores:
            detailed_lines.append("(Algún cofactor no es representable en coma flotante a esta escala: "
                                  "la matriz de cofactores y Adj(A)/det(A) no son confiables; "
                                  "A⁻¹ por Gauss-Jordan sí.)")
        if detA != 0.0 and not math.isinf(detA) and not avisos_cofactores:
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
            # Residuo relativo por componente: |(Ax)_i - b_i| frente a la
            # magnitud de los términos que lo forman. El 1e-9 absoluto de
            # antes aceptaba cualquier x si A y b eran ~1e-10, y rechazaba
            # soluciones correctas si eran ~1e10.
            ok = all(
                abs(Ax[i] - b[i]) <= 1e-9 * (sum(abs(A[i][j] * x[j]) for j in range(n)) + abs(b[i]))
                for i in range(len(b))
            )
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