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
    
     # ----------------------
    # Fase 1: Eliminación hacia adelante (triangulación superior)
    # ----------------------
    def forward_elimination(self) -> List[Tuple[int, int]]:
        """
        Genera ceros por DEBAJO de los pivotes (forma triangular superior).
        Registra pivotes y operaciones en self.frame.
        """
        m = self.filas
        n_plus_1 = self.columnas
        n = n_plus_1 - 1  # solo columnas de coeficientes

        log_step(self.frame, "Matriz aumentada inicial", self.matriz, det=None, tag="start")

        row = 0
        pivots: List[Tuple[int, int]] = []
        for col in range(n):
            if row >= m:
                break

            sel = self._select_pivot_row(row, col)
            if sel == -1:
                # Columna sin pivote significativo
                log_step(self.frame, f"No hay pivote significativo en la columna {col+1}", self.matriz, det=None, tag="no_pivot")
                continue

            if sel != row:
                self._swap_rows(row, sel)

            pivot_val = self.matriz[row][col]
            log_step(self.frame, f"Pivote en A[{row+1},{col+1}] = {format_number(pivot_val)}", self.matriz, det=None, tag="pivot")

            # Eliminar hacia abajo
            for r in range(row + 1, m):
                self._row_elim(r, row, col)

            pivots.append((row, col))
            row += 1

        self.pivots = pivots
        log_step(self.frame, "Triangulación superior (U)", self.matriz, det=None, tag="upper")
        return pivots

    # ----------------------
    # Fase 2: Normalizar pivotes y eliminar arriba (RREF)
    # ----------------------
    def backward_elimination_and_normalize(self) -> None:
        """
        Lleva la matriz a RREF:
          - pivotes normalizados a 1
          - ceros arriba y abajo de cada pivote
        """
        if not self.pivots:
            self.forward_elimination()

        # Normalizar cada pivote a 1 (de abajo a arriba) y eliminar arriba
        for (r, c) in reversed(self.pivots):
            piv = self.matriz[r][c]
            if isclose(piv, 0.0, abs_tol=self.tolerance):
                continue
            # Diagonal de 1
            self._scale_row(r, piv)

            # Ceros ARRIBA del pivote
            for rr in range(0, r):
                self._row_elim(rr, r, c)

        log_step(self.frame, "Forma reducida por filas (RREF)", self.matriz, det=None, tag="rref")

    # ----------------------
    # Orquestador
    # ----------------------
    def run(self) -> Dict[str, Dict[str, Any]]:
        """Ejecuta Gauss-Jordan completo con logs."""
        self.frame = {}
        self.forward_elimination()
        self.backward_elimination_and_normalize()
        return self.frame

    # ----------------------
    # Análisis y solución
    # ----------------------
    def analyze(self) -> Dict[str, Any]:
        """
        Analiza [A|b] actual (tras forward/RREF) con analyze_argumented:
          - rank, pivots, basic/free vars, filas inconsistentes y status
        """
        return analyze_argumented(self.matriz, tol=self.tolerance)

    def solve_and_log(self) -> Dict[str, Any]:
        """
        Produce resumen y solución particular (si existe) reutilizando solve_from_upper.
        Nota: aunque estamos en RREF, la rutina de back-sub funciona igual.
        """
        info = self.analyze()
        status = info.get("status")
        pivots = info.get("pivots", [])
        log_step(self.frame, f"Resumen: Tipo de solución = {status}", self.matriz, det=None, tag="summary")

        if status == "inconsistent":
            log_step(self.frame, "Sistema inconsistente: no existe solución", self.matriz, det=None, tag="inconsistent")
            return {**info, "solution": None}

        # Solución particular (variables libres = 0)
        result = solve_from_upper(self.matriz, pivots=pivots, tol=self.tolerance)
        sol = result.get("solution")
        if sol is not None:
            sol_str = [format_number(v) for v in sol]
            log_step(self.frame, f"Solución particular (libres=0): [{', '.join(sol_str)}]", self.matriz, det=None, tag="solution")

        basic = result.get("basic_vars", [])
        free = result.get("free_vars", [])
        def idxs_to_vars(idxs): return "None" if not idxs else ", ".join(f"x{(i+1)}" for i in idxs)
        log_step(self.frame, f"Variables básicas: {idxs_to_vars(basic)} | Variables libres: {idxs_to_vars(free)}", self.matriz, det=None, tag="vars")

        return result

    # ----------------------
    # Chequeos útiles
    # ----------------------
    def is_singular(self) -> Optional[bool]:
        """
        Solo tiene sentido para A cuadrada.
        Regresa True si rank(A) < n usando el análisis de la aumentada.
        """
        # n = columnas de coeficientes
        n = self.columnas - 1
        m = self.filas
        if n != m:
            return None  # no aplica (A no es cuadrada)
        info = self.analyze()
        return info.get("rank", 0) < n
        
            
