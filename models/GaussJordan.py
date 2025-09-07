from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple
from math import isclose 
from models.Matrix import Matrix
from utils.printMethods import log_step
from utils.EquationFunctions import format_number
from models.system_solver.GaussSolver import analyze_argumented, solve_from_upper

class GaussJordanMethod(Matrix):
    """
    Método de Gauss-Jordan con:
      - Soporte m x n (rectangulares) con matriz A y vector b (matriz aumentada).
      - Registro detallado de operaciones en self.frame (swap, escalar, eliminación, upper, rref, summary).
      - Detección de pivotes, variables básicas y libres, e inconsistencias.
      - Triangulación superior y reducción total a RREF (ceros arriba/abajo y diagonal 1).
      - Chequeos de singularidad para A cuadrada.
    Uso típico:
        mat, b = Matrix.make_equation(m, n)      # <— solo este camino
        gj = GaussJordanMethod(mat, b)
        gj.run()                                  # forward + backward (RREF) con logs
        result = gj.solve_and_log()               # analiza tipo de solución y da solución particular
    """
    
    def __init__(self, matriz: List[List[float]], b: Optional[List[float]]) -> None:
        if b is None:
            raise ValueError("GaussJordanMethod requiere A y b (usa Matrix.make_equation).")
        
        if len(b) != len(matriz):
            raise ValueError("El vector b debe tener la misma cantidad de filas que A.")
        
        # Construir matriz aumentada [A | b]
        aug = [list(map(float, row)) + [float(bi)] for row, bi in zip(matriz, b)]
        super().__init__(copy.deepcopy(aug))
        
        # Metadatos
        self.is_argumented: bool = True
        self.A: List[List[float]] = copy.deepcopy(matriz)
        self.b: List[float] = copy.deepcopy(b)
        
        # Log y tolerancias
        self.tolerance = bool = True
        self.frame = Dict[str, Dict[str, Any]] = {}
        self.pivots: List[Tuple[int, int]] = []   # lista de (fila, col) de pivotes detectados en forward

        # Determinante: solo relevante si A es cuadrada y no escalamos (aquí se escala para RREF),
        # así que lo mantenemos informativo (no lo reportamos).
        self.determinante: Optional[float] = None
        
    # ----------------------
    # Helpers numéricos
    # ----------------------
    def _zero_small(self, x: float) -> float:
        return 0.0 if isclose(x, 0.0, abs_tol=self.tolerance) else x

    # ----------------------
    # Operaciones elementales (con log)
    # ----------------------
    def _swap_rows(self, r1: int, r2: int) -> None:
        if r1 == r2:
            return
        self.matriz[r1], self.matriz[r2] = self.matriz[r2], self.matriz[r1]
        log_step(self.frame, f"F{r1+1} <-> F{r2+1}", self.matriz, det=None, tag="swap_rows")
        
    def _scale_row(self, r: int, factor: float) -> None:
        if isclose(factor, 1.0, abs_tol=self.tolerance):
            return
        if isclose(factor, 0.0, abs_tol=self.tolerance):
            raise ValueError("No se puede escalar por 0.")
        self.matriz[r] = [self._zero_small(v / factor) for v in self.matriz[r]]
        log_step(self.frame, f"F{r+1} -> F{r+1} / {format_number(factor)}", self.matriz, det=None, tag="scale")
        
    def _row_elim(self, target_r: int, pivot_r: int, pivot_c: int) -> None:
        """F_target := F_target - factor * F_pivot para anular columna pivot_c."""
        factor = self.matriz[target_r][pivot_c]
        if isclose(factor, 0.0, abs_tol=self.tolerance):
            return
        row_len = len(self.matriz[0])
        for j in range(pivot_c, row_len):
            self.matriz[target_r][j] = self._zero_small(self.matriz[target_r][j] - factor * self.matriz[pivot_r][j])
        signo = "+" if factor < 0 else "-"
        log_step(self.frame,
                 f"F{target_r+1} -> F{target_r+1} {signo} {format_number(abs(factor))}*F{pivot_r+1}",
                 self.matriz, det=None, tag="elim")
        
    # ----------------------
    # Pivoteo parcial por filas
    # ----------------------
    def _select_pivot_row(self, start_row: int, col: int) -> int:
        """Devuelve fila con |A[row][col]| máximo desde start_row, o -1 si la columna es casi cero."""
        best = -1
        best_val = 0.0
        for r in range(start_row, self.filas):
            val = abs(self.matriz[r][col])
            if val > best_val:
                best_val = val
                best = r
        if isclose(best_val, 0.0, abs_tol=self.tolerance):
            return -1
        return best
    
    
        
            
