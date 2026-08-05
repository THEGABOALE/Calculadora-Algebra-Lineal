"""
MÉTODO DE GAUSS (eliminación hacia adelante) CON LOGS

Propósito
- Triangular la matriz aumentada [A | b] y resolver por sustitución hacia atrás.
- Registrar cada paso en `self.frame`, igual que Gauss-Jordan.

Contrato (dos pasos, el mismo que GaussJordanMethod)
    g = GaussMethod(A, b)
    g.gauss_method()        # elimina y deja self.matriz en forma triangular
    r = g.solve_and_log()   # sólo analiza y resume lo ya eliminado

Pivoteo parcial POR FILAS. No se intercambian columnas: hacerlo permuta las
variables y aquí no hay forma de deshacer esa permutación al presentar la
solución. Ver el commit que unificó este archivo para la evidencia.

Dependencias (internas)
- core.matrix.Matrix
- core.system_solver.gauss_solver (analyze_argumented, solve_from_upper)
- utils.printMethods (log_step)

El runner interactivo vive en cli.method_runners; aquí no se imprime nada.
"""

from core.matrix import Matrix
from math import isclose
import copy
from typing import Any, Dict, List, Optional, Tuple

from core.system_solver.gauss_solver import solve_from_upper, analyze_argumented
from utils.printMethods import log_step

from utils.EquationFunctions import format_number, num_to_sub

class GaussMethod(Matrix):
    def __init__(self, matriz: List[List[float]], b: Optional[List[float]]) -> None:
        if b is not None:
            if len(b) != len(matriz):
                raise ValueError("El vector b ebe tener misma cantidad de filas que la matriz")
            aug = [list(map(float, row)) + [float(bi)] for row, bi in zip(matriz, b)]
            super().__init__(copy.deepcopy(aug))
            self.is_augmented = True
            self.A = copy.deepcopy(matriz)
            self.b = copy.deepcopy(b)
        else:
            super().__init__(copy.deepcopy(matriz))
            self.is_augmented = False
            self.A = copy.deepcopy(matriz)
            self.b = None
        self.determinante:float = 1.0
        self.tolerance = 1e-13 # Notacion cientifica
        self.frame: Dict[str, Dict[str, Any]] = {}
        self.pivots: List[Tuple[int,int]] = []
        self.analize: Dict[str, Any] = {}

    def gauss_method(self) -> dict[str, dict[str, any]]:
        # Unifica el registro de pasos y la lógica de resolución, como en Gauss-Jordan
        self.frame = {}
        self.determinante = 1.0
        if not getattr(self, "is_augmented", False):
            raise RuntimeError("La instancia no contiene una matriz aumentada")
        aug = self.matriz
        m = len(aug)
        if m == 0:
            return self.frame
        n_plus_1 = len(aug[0])
        n = n_plus_1 - 1
        row = 0
        pivots: List[Tuple[int,int]] = []
        log_step(self.frame, "Matriz aumentada inicial", aug, det=None, tag="start")
        # Chequeo de matriz singular antes de operar
        if self.filas == self.columnas and self.null_determinant():
            return self.frame
        for col in range(n):
            if row >= m:
                break
            sel = max(range(row, m), key=lambda r: abs(aug[r][col]))
            if isclose(aug[sel][col], 0.0, abs_tol=self.tolerance):
                log_step(self.frame, f"No hay pivote significativo en la columna {col+1}", aug, det=None, tag="no_pivot")
                continue
            if sel != row:
                self.swipe_rows(row, sel)
            pivots.append((row, col))
            pivot_val = aug[row][col]
            log_step(self.frame, f"Pivote en A[{row+1},{col+1}] = {format_number(pivot_val)}", aug, det=None, tag="pivot")
            for r in range(row + 1, m):
                if isclose(aug[r][col], 0.0, abs_tol=self.tolerance):
                    continue
                factor = aug[r][col] / pivot_val
                for c in range(col, n + 1):
                    aug[r][c] -= factor * aug[row][c]
                    if isclose(aug[r][c], 0.0, abs_tol=self.tolerance):
                        aug[r][c] = 0.0
                log_step(self.frame, f"F{r+1} -> F{r+1} - ({format_number(factor)})*F{row+1}", aug, det=None, tag="elim")
            row += 1
        self.matriz = aug
        self.filas = len(aug)
        self.columnas = len(aug[0]) if aug else 0
        self.pivots = pivots
        log_step(self.frame, "Matriz aumentada triangular superior (U)", self.matriz, det=None, tag="upper")
        if self.filas == self.columnas:
            self.determinant_result()
        return self.frame

    def fordward_elimination_aug(self) -> Tuple[List[List[float]], List[Tuple[int,int]]]:
        if not getattr(self, "is_augmented", False):
            raise RuntimeError("La instancia no contiene una matriz aumentada")
        aug = self.matriz
        m = len(aug)
        if m == 0:
            return aug, []
        n_plus_1 = len(aug[0])
        n = n_plus_1 - 1
        row = 0
        pivots: List[Tuple[int,int]] = []
        log_step(self.frame, "Matriz aumentada inicial", aug, det=None, tag="start")
        for col in range(n):
            if row >= m: break
            sel = max(range(row, m), key=lambda r: abs(aug[r][col]))
            if isclose(aug[sel][col], 0.0, abs_tol=self.tolerance):
                log_step(self.frame, f"No hay pivote significativo en la columna {col+1}", aug, det=None, tag="no_pivot")
                continue
            if sel != row:
                self.swipe_rows(row, sel)
            pivots.append((row, col))
            pivot_val = aug[row][col]
            log_step(self.frame, f"Pivote en A[{row+1},{col+1}] = {format_number(pivot_val)}", aug, det=None, tag="pivot")
            for r in range(row + 1, m):
                if isclose(aug[r][col], 0.0, abs_tol=self.tolerance):
                    continue
                factor = aug[r][col] / pivot_val
                for c in range(col, n + 1):
                    aug[r][c] -= factor * aug[row][c]
                    if isclose(aug[r][c], 0.0, abs_tol=self.tolerance):
                        aug[r][c] = 0.0
                log_step(self.frame, f"F{r+1} -> F{r+1} - ({format_number(factor)})*F{row+1}", aug, det=None, tag="elim")
            row += 1
        self.matriz = aug
        self.filas = len(aug)
        self.columnas = len(aug[0]) if aug else 0
        self.pivots = pivots
        log_step(self.frame, "Matriz aumentada triangular superior (U)", self.matriz, det=None, tag="upper")
        return self.matriz, pivots

    def solve_and_log(self) -> Dict[str, Any]:
        # Solo analiza y resume, asume que gauss_method ya fue ejecutado
        if not getattr(self, "is_augmented", False):
            raise RuntimeError("La instancia no contiene una matriz aumentada")
        result = solve_from_upper(self.matriz, pivots=self.pivots)
        status = result.get('status')
        sol = result.get('solution')
        basic = result.get('basic_vars',[])
        free = result.get('free_vars',[])
        def idxs_to_vars(idxs):
            if not idxs: return "None"
            return ", ".join(f"x{num_to_sub(i+1)}" for i in idxs)
        log_step(self.frame, f"Resumen: Tipo de solucion = {status}", self.matriz, det=None, tag="summary")
        if status == 'inconsistent':
            log_step(self.frame, "Sistema inconsistente: no existe solución", self.matriz, det=None, tag="inconsistent")
        else:
            if sol is not None:
                sol_str = [format_number(val) for val in sol]
                log_step(self.frame, f"Solución particular (libres=0): [{', '.join(sol_str)}]", self.matriz, det=None, tag="solution")
            log_step(self.frame, f"Variables básicas: {idxs_to_vars(basic)} | Variables libres: {idxs_to_vars(free)}", self.matriz, det=None, tag="vars")
        return result

    def null_determinant(self) -> bool:
        if self.filas != self.columnas:
            return False
        for row in range(self.filas):
            if all(self.matriz[row][i]==0 for i in range(self.columnas)):
                log_step(self.frame, f"Fila {row+1} son 0, su determinante es 0 (Matriz Singular)", self.matriz, det=0, tag="singular")
                return True
        for col in range(self.columnas):
            if all(self.matriz[i][col]==0 for i in range(self.filas)):
                log_step(self.frame, f"Columna {col+1} son 0, su determinante es 0 (Matriz Singular)", self.matriz, det=0, tag="singular")
                return True
        for i in range(self.filas):
            for j in range(i+1, self.filas):
                if self.matriz[i] == self.matriz[j]:
                    log_step(self.frame, f"Filas {i+1} y {j+1} son iguales, su determinmante es 0 (Matriz Singular)", self.matriz, det=0, tag="singular")
                    return True
        for i in range(self.columnas):
            for j in range(i+1, self.columnas):
                col_i = [self.matriz[k][i] for k in range(self.filas)]
                col_j = [self.matriz[k][j] for k in range(self.filas)]
                if col_i == col_j:
                    log_step(self.frame, f"Columnas {i+1} y {j+1} son iguales, su determinante es 0 (Matriz Singular)", self.matriz, det=0, tag="singular")
                    return True
        return False

    def determinant_result(self):
        if self.filas != self.columnas:
            return 
        diag_product = 1.0
        limit = min(self.filas, self.columnas)
        for i in range(limit):
            diag_product *= self.matriz[i][i]
        final_dect = self.determinante * diag_product
        details = f"Determinante = ({format_number(self.determinante)})" + "".join(f"({format_number(self.matriz[i][i])})" for i in range(limit))
        log_step(self.frame, details, self.matriz, det=format_number(float(final_dect)), tag="det")

    def swipe_rows(self, fila_a, fila_b) -> None:
        temp = self.matriz[fila_a]
        self.matriz[fila_a] = self.matriz[fila_b]
        self.matriz[fila_b] = temp
        if self.filas == self.columnas:
            self.determinante *= -1.0
        log_step(self.frame, f"Fila {fila_a+1} <-> Fila {fila_b+1}", self.matriz,
                det=(format_number(self.determinante) if self.filas == self.columnas else None), tag="swap_rows")

__all__ = ['GaussMethod']
