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

Uso (típico):
# A: matriz mxn, b: vector de longitud m
aug = [row[:] + [b_i] for row, b_i in zip(A, b)]

# o bien: usar GaussMethod.forward_elimination_aug para triangularizar `aug`
U, pivots = gauss.forward_elimination_aug(aug)

# o llamar a analizar/resolver directamente en U (triangular superior aumentada)
info = analizar_aumentado(U)
res = resolver_desde_arriba(U, info['pivotes'])

El módulo es intencionalmente pequeño y sin dependencias.
"""
from typing import Any, Dict, List, Optional, Tuple
from math import isclose

def find_pivots_from_upper(U: List[List[float]], tol: float=1e-12) -> List[Tuple[int,int]]:
    """
    Devuelve la lista de posiciones pivote (fila, columna) de una matriz triangular 
    superior U (matriz aumentada con la última columna = RHS). 
    Se asume que U es el resultado de la eliminación hacia delante 
    (forma triangular). Se escanea cada fila y se toma como pivote 
    la primera columna con valor absoluto > tol.
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
            if not isclose(U[r][c], 0.0, abs_tol=tol):
                pivot_col = c
                break
        if pivot_col != -1:
            pivots.append((r, pivot_col))
    return pivots

def analyze_argumented(U: List[List[float]], tol: float=1e-12) -> Dict[str, Any]:
    """
    Analiza una matriz aumentada U (m x (n+1)) y devuelve:
        {
        'm': m,
        'n': n,
        'pivots': [(r,c), ...],
        'rank': rank,
        'basic_vars': [cols...],
        'free_vars': [cols...],
        'inconsistent_rows': [r,...],
        'status': 'unique'|'infinite'|'inconsistent'
        }

    Nota: Esta función solo *analiza* U tal como está. No realiza eliminación; 
    espera que U esté en forma triangular superior (o al menos que ya se haya 
    aplicado la eliminación hacia delante).
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
        all_zero_coeffs = all(isclose(U[r][c], 0.0, abs_tol=tol) for c in range(n) )
        rhs_nonzero = not isclose(U[r][n], 0.0, abs_tol=tol)
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
    
def solve_from_upper(U: List[List[float]], pivots: Optional[List[Tuple[int,int]]] = None, tol: float = 1e-12, col_permutation: Optional[List[int]]=None) -> Dict[str, Any]:
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
        if isclose(pivot_val, 0.0, abs_tol=tol):
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

def solve_system_direct(A: List[List[float]], b: List[float], tol: float=1e-12) -> Dict[str, Any]:
    '''
    Construye una matriz aumentada, realiza una eliminación directa simple con pivoteo parcial 
    (solo filas), analiza y resuelve.
    Este es un asistente autónomo útil para pruebas y comprobaciones rápidas.
    Devuelve el mismo diccionario que solve_from_upper.
    '''
    m = len(A)
    if m == 0:
        return {'status': 'unique', 'solution': [], 'pivots': [], 'basic_vars': [], 'free_vars': [], 'rank': 0}
    n = len(A[0])
    aug = [List(map(float, A[r])) + [float(b[r])] for r in range(m)]
    
    row = 0
    pivots: List[Tuple[int, int]] = []
    for col in range(n):
        if row >= m:
            break
        sel = max(range(row, m), key=lambda rr: abs(aug[rr][col]))
        if isclose(aug[sel][col], 0.0, abs_tol=tol):
            continue
        if sel != row:
            aug[row], aug[sel] = aug[sel], aug[row]
        pivots.append((row,col))
        pivots_val = aug[row][row]
        for r in range(row + 1, m): 
            if isclose(aug[r][col], 0.0, abs_tol=tol):
                continue
            factor = aug[r][col] / pivots_val
            for c in range(col, n+1):
                aug[r][c] -= factor * aug[row][c]
                if isclose(aug[r][c], 00, abs_tol=tol):
                    aug[r][c] =0.0
        row += 1
    
    # Analizar y resolver
    info = analyze_argumented(aug, tol=tol)
    return solve_from_upper(aug, pivots=pivots, tol=tol)