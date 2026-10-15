"""
Pequeño módulo auxiliar para analizar y resolver sistemas lineales a partir de
una matriz aumentada triangular superior (eliminada hacia delante).

Objetivos de diseño:
- Mantener el método de Gauss centrado en la eliminación y el registro. Proporcionar utilidades pequeñas y bien probadas que toman la matriz *aumentada*
    tras la eliminación hacia delante y:
        * detectar pivotes
        * clasificar variables básicas/libres
        * detectar inconsistencias
        * calcular una solución numérica (particular) mediante sustitución hacia atrás

Qué es "cero" acá
-----------------
Estas funciones NO deciden qué número es ruido de redondeo: eso lo decide la
eliminación que produjo U (GaussMethod, GaussJordanMethod, solve_system_direct),
con el criterio de core/matrix_tools.py (CotasDeRedondeo: una entrada es cero
si es menor que el redondeo que pudo acumular al calcularla), y lo deja escrito
como 0.0 EXACTO. Por eso, con `tol=None` (el default), un valor es cero sii es
exactamente 0.0.

Antes el default era un umbral absoluto 1e-12 aplicado a la matriz final: con
coeficientes ~1e-13 no encontraba pivotes, con un b_i = 1e-13 real tomaba
"0 = 1e-13" por "0 = 0", y con coeficientes ~1e8 tomaba el ruido por dato. Un
`tol` numérico explícito se sigue aceptando como umbral absoluto, para quien
pase una matriz que no salió de esas eliminaciones.

Uso (típico):
# A: matriz mxn, b: vector de longitud m
g = GaussMethod(A, b); g.gauss_method()      # U escalonada, ruido en 0.0
info = analyze_argumented(g.matriz)
res = solve_from_upper(g.matriz, pivots=g.pivots)

# o, sin registro de pasos:
res = solve_system_direct(A, b)

El módulo es intencionalmente pequeño y sin dependencias externas.
"""
from typing import Any, Dict, List, Optional, Tuple
from math import isclose


def _es_nulo(x: float, tol: Optional[float]) -> bool:
    """Cero exacto (tol=None) o, si se pide, bajo un umbral absoluto."""
    if tol is None:
        return x == 0.0
    return isclose(x, 0.0, abs_tol=tol)


def find_pivots_from_upper(U: List[List[float]], tol: Optional[float] = None) -> List[Tuple[int,int]]:
    """
    Devuelve la lista de posiciones pivote (fila, columna) de una matriz triangular
    superior U (matriz aumentada con la última columna = RHS).
    Se asume que U es el resultado de la eliminación hacia delante
    (forma triangular). Se escanea cada fila y se toma como pivote
    la primera columna de coeficientes distinta de cero.
    """

    m = len(U)
    if m == 0:
        return []
    n_plus_1 = len(U[0])
    n = n_plus_1 - 1
    pivots: List[Tuple[int,int]] = []

    for r in range(m):
        pivot_col = -1
        for c in range(n):
            if not _es_nulo(U[r][c], tol):
                pivot_col = c
                break
        if pivot_col != -1:
            pivots.append((r, pivot_col))
    return pivots

def analyze_argumented(U: List[List[float]], tol: Optional[float] = None) -> Dict[str, Any]:
    """
    Analiza una matriz aumentada U (m x (n+1)) y devuelve:
        {
        'm': m,
        'n': n,
        'pivots': [(r,c), ...],
        'rank': rank,              # rango de A (sólo columnas de coeficientes)
        'basic_vars': [cols...],
        'free_vars': [cols...],
        'inconsistent_rows': [r,...],
        'status': 'unique'|'infinite'|'inconsistent'
        }

    Nota: Esta función solo *analiza* U tal como está. No realiza eliminación;
    espera que U esté en forma escalonada (triangular superior o RREF) y que
    la eliminación ya haya dejado el ruido de redondeo en 0.0 (ver el
    docstring del módulo).
    """
    m = len(U)
    if m == 0:
        return {
            'm': 0,
            'n': 0,
            'pivots': [],
            'rank': 0,
            'basic_vars': [],
            'free_vars': [],
            'inconsistent_rows': [],
            'status': 'unique'
        }

    n_plus_1 = len(U[0])
    n = n_plus_1 - 1
    pivots = find_pivots_from_upper(U, tol=tol)
    pivots_cols = [col for (_r, col) in pivots]
    rank = len(pivots)

    inconsistent_rows: List[int] = []
    for r in range(m):
        all_zero_coeffs = all(_es_nulo(U[r][c], tol) for c in range(n))
        rhs_nonzero = not _es_nulo(U[r][n], tol)
        if all_zero_coeffs and rhs_nonzero:
            inconsistent_rows.append(r)

    # Clasificacion de variables
    basic_vars = pivots_cols.copy()
    free_vars = [j for j in range(n) if j not in pivots_cols]

    # Manejo de soluciones
    if inconsistent_rows:
        status = 'inconsistent'
    elif rank == n:
        status = 'unique'
    else: status = 'infinite'

    return {
        'm': m,
        'n': n,
        'pivots': pivots,
        'rank': rank,
        'basic_vars': basic_vars,
        'free_vars': free_vars,
        'inconsistent_rows': inconsistent_rows,
        'status': status
    }

def solve_from_upper(U: List[List[float]], pivots: Optional[List[Tuple[int,int]]] = None, tol: Optional[float] = None, col_permutation: Optional[List[int]]=None) -> Dict[str, Any]:
    """
    Dada una matriz triangular superior aumentada U (m x (n+1)) y, opcionalmente,
    una lista de pivotes (fila, columna), calcule una solución numérica mediante
    sustitución inversa.

    Devuelve un diccionario con las siguientes claves:
    - 'status': 'unique'|'infinite'|'inconsistent'
    - 'solution': list[float] (una solución particular) o None
    - 'basic_vars', 'free_vars', 'pivots', 'rank', 'inconsistent_rows'

    Si pivots es None, la función llamará a la función Analyze_augmented para
    calcularla.
    Si se proporciona la permutación de columnas
    (mapeo de lista current_col -> original_col), el vector de solución
    devuelto se reasignará al orden de variables original.
    """
    info = analyze_argumented(U, tol=tol)
    if pivots is None:
        pivots = info['pivots']

    status = info['status']
    m = info['m']
    n = info['n']

    if status == 'inconsistent':
        return {**info, 'solution': None}

    ''' Crear una solución particular: librerar vars = 0 y sustituir hacia atras '''
    x = [0.0] * n

    ''' Los pivotes podrian no estar ordenados: asegurar el orden inverso de las filas '''
    pivots_sorted = sorted(pivots, key=lambda rc: rc[0])

    for (r, c) in reversed(pivots_sorted):
        rhs = U[r][n]
        s = rhs
        for j in range(c + 1,n):
            s -= U[r][j]*x[j]
        pivot_val = U[r][c]
        if _es_nulo(pivot_val, tol):
            x[c] = 0.0
        else:
            x[c] = s / pivot_val

    ''' Si se proporciona el mapeo de permutacion, se reasigna la solucion al orden original '''
    if col_permutation:
        ''' col_permutation mapea current_index -> original_index '''
        remapped = [0.0] * len(col_permutation)
        for current_index, original_index in enumerate(col_permutation):
            if original_index < len(x):
                remapped[original_index] = x[current_index]
        x = remapped

    return {**info, 'solution': x}

def solve_system_direct(A: List[List[float]], b: List[float], tol: Optional[float] = None) -> Dict[str, Any]:
    '''
    Construye una matriz aumentada, realiza una eliminación hacia adelante con
    pivoteo parcial (sólo filas), analiza y resuelve. Sin registro de pasos:
    es un asistente autónomo para pruebas y comprobaciones rápidas, que acepta
    A rectangular.
    Devuelve el mismo diccionario que solve_from_upper.

    Correcciones respecto de la versión anterior, que nunca llegó a ejecutarse:
    - `List(map(...))` llamaba al genérico `typing.List`, que no se puede
      instanciar: TypeError en cualquier entrada no vacía.
    - el pivote se leía de aug[row][row] en vez de aug[row][col]: con una
      columna sin pivote antes (col > row) dividía por la entrada equivocada.
    - el umbral absoluto 1e-12 en pivotes y limpieza se reemplaza por el
      criterio de core/matrix_tools.py (con `tol` numérico, umbral absoluto).
    - con m == 0 devolvía un dict sin 'n', 'inconsistent_rows' ni 'm'.
    '''
    # Import local: core.matrix_tools no depende de este módulo, pero así
    # quien sólo use analyze_argumented/solve_from_upper no lo carga.
    from core.matrix_tools import CotasDeRedondeo, restar_multiplo_de_fila

    m = len(A)
    if len(b) != m:
        raise ValueError("El vector b debe tener tantas entradas como filas tiene A.")
    if m == 0:
        return solve_from_upper([], tol=tol)
    n = len(A[0])
    if any(len(fila) != n for fila in A):
        raise ValueError("Todas las filas de A deben tener la misma cantidad de columnas.")
    aug = [list(map(float, A[r])) + [float(b[r])] for r in range(m)]
    cotas = CotasDeRedondeo(aug, tol=tol)

    row = 0
    pivots: List[Tuple[int, int]] = []
    for col in range(n):
        if row >= m:
            break
        candidatos = [rr for rr in range(row, m)
                      if aug[rr][col] != 0.0 and not cotas.es_cero(aug[rr][col], rr, col)]
        if not candidatos:
            for rr in range(row, m):
                aug[rr][col] = 0.0
            continue
        sel = max(candidatos, key=lambda rr: abs(aug[rr][col]))
        if sel != row:
            aug[row], aug[sel] = aug[sel], aug[row]
            cotas.intercambiar(row, sel)
        pivots.append((row, col))
        pivot_val = aug[row][col]
        for r in range(row + 1, m):
            if aug[r][col] == 0.0:
                continue
            if cotas.es_cero(aug[r][col], r, col):
                aug[r][col] = 0.0
                continue
            restar_multiplo_de_fila(aug, cotas, r, row, aug[r][col], pivot_val, desde=col)
            aug[r][col] = 0.0
            for c in range(col + 1, n + 1):
                if cotas.es_cero(aug[r][c], r, c):
                    aug[r][c] = 0.0
        row += 1

    # Cada entrada actualizada (también la columna b) ya pasó por el criterio
    # al calcularse: lo que es ruido quedó en 0.0, así que "0 = c" en una fila
    # sin pivote es un c real (incompatible). Análisis exacto.
    return solve_from_upper(aug, pivots=pivots)
