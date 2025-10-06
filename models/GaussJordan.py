"""
GAUSS–JORDAN (RREF) CON LOGS

Propósito
- Resolver sistemas lineales trabajando sobre la matriz aumentada [A | b].
- Llevar la matriz a forma reducida por filas (RREF): pivotes = 1 y ceros
  arriba/abajo de cada pivote.

Características
- Soporta matrices rectangulares m×n (A) con vector b (longitud m).
- Pivoteo parcial por filas (no intercambia columnas).
- Registro de pasos en `self.frame` mediante `utils.printMethods.log_step`.
- Detección de tipo de solución, variables básicas/libres e inconsistencias
  usando `analyze_argumented` y solución particular con `solve_from_upper`.

Entradas
- A: list[list[float]]     b: list[float] (len(b) == filas(A))

Dependencias (internas)
- models.Matrix.Matrix (para estructura y pretty-print de matriz)
- utils.printMethods (log_step, print_frame, print_equation, print_summary)
- models.system_solver.GaussSolver (analyze_argumented, solve_from_upper)
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple
from math import isclose 
from models.Matrix import Matrix
from utils.printMethods import log_step, print_summary, print_equation, print_frame
from linear_algebra_calculator.utils.EquationFunctions import format_number
from models.system_solver.GaussSolver import analyze_argumented, solve_from_upper
from helpers.inputsmatrix import inputs_matrix

class GaussJordanMethod(Matrix):
    """
    Implementación de Gauss–Jordan sobre [A | b].

    - Forward: triangulación superior (ceros debajo de pivotes).
    - Backward + normalize: RREF (pivotes = 1 y ceros arriba/abajo).
    - Registro de operaciones y análisis del sistema.

    Uso típico:
        A, b = Matrix.make_equation(m, n)
        gj = GaussJordanMethod(A, b)
        gj.run()                 # RREF con logs
        result = gj.solve_and_log()
    """
    
    def __init__(self, matriz: List[List[float]], b: Optional[List[float]]) -> None:
        if b is None:
            raise ValueError("GaussJordanMethod requiere A y b (usa Matrix.make_equation).")
        
        if len(b) != len(matriz):
            raise ValueError("El vector b debe tener la misma cantidad de filas que A.")
        
        # Construir matriz aumentada [A | b] y delegar tamaños a Matrix
        aug = [list(map(float, row)) + [float(bi)] for row, bi in zip(matriz, b)]
        super().__init__(copy.deepcopy(aug))
        
        # Metadatos
        self.is_augmented: bool = True
        self.A: List[List[float]] = copy.deepcopy(matriz)
        self.b: List[float] = copy.deepcopy(b)
        
        # Log y tolerancias
        self.tolerance: float = 1e-12
        self.frame: Dict[str, Dict[str, Any]] = {}
        self.pivots: List[Tuple[int, int]] = []   # lista de (fila, col) de pivotes detectados en forward

        # Determinante: solo relevante si A es cuadrada y no escalamos (aquí se escala para RREF),
        # así que lo mantenemos informativo (no lo reportamos).
        self.determinante: Optional[float] = None

        #Cambios nuevos Sistemas homogeneos/ No homogeneos || Dependientes y no dependientes. 

                # Validaciones adicionales
        if not matriz or not all(isinstance(row, list) for row in matriz):
            raise ValueError("La matriz A no puede estar vacía y debe ser una lista de listas.")

        cols = len(matriz[0])
        if not all(len(row) == cols for row in matriz):
            raise ValueError("Todas las filas de la matriz A deben tener la misma cantidad de columnas.")

        for row in matriz:
            for val in row:
                if not isinstance(val, (int, float)):
                    raise TypeError("Todos los elementos de A deben ser numéricos (int o float).")
        for val in b:
            if not isinstance(val, (int, float)):
                raise TypeError("Todos los elementos del vector b deben ser numéricos (int o float).")

        # Detección de homogeneidad
        self.is_homogeneous: bool = all(isclose(bi, 0.0, abs_tol=self.tolerance) for bi in b)
        msg = "Sistema homogéneo (b = 0)" if self.is_homogeneous else "Sistema no homogéneo (b ≠ 0)"
        log_step(self.frame, msg, aug, det=None, tag="homogeneity_check")

        
    # ----------------------
    # Helpers numéricos
    # ----------------------
    def _zero_small(self, x: float) -> float:
        """Lleva a 0 valores muy pequeños para limpiar el formato."""
        return 0.0 if isclose(x, 0.0, abs_tol=self.tolerance) else x

    # ----------------------
    # Operaciones elementales (con log)
    # ----------------------
    def _swap_rows(self, r1: int, r2: int) -> None:
        """Intercambia filas y registra el paso (no cambia determinante aquí)."""
        if r1 == r2:
            return
        self.matriz[r1], self.matriz[r2] = self.matriz[r2], self.matriz[r1]
        log_step(self.frame, f"F{r1+1} <-> F{r2+1}", self.matriz, det=None, tag="swap_rows")
        
    def _scale_row(self, r: int, factor: float) -> None:
        """Normaliza fila: F_r := F_r / factor (factor ≠ 0)."""
        if isclose(factor, 1.0, abs_tol=self.tolerance):
            return
        if isclose(factor, 0.0, abs_tol=self.tolerance):
            raise ValueError("No se puede escalar por 0.")
        self.matriz[r] = [self._zero_small(v / factor) for v in self.matriz[r]]
        log_step(self.frame, f"F{r+1} -> F{r+1} / {format_number(factor)}", self.matriz, det=None, tag="scale")
        
    def _row_elim(self, target_r: int, pivot_r: int, pivot_c: int) -> None:
        """
        Eliminación en columna pivot_c:
            F_target := F_target - (A[target,pivot_c]/A[pivot_r,pivot_c]) * F_pivot
        """
        pivot_val = self.matriz[pivot_r][pivot_c]
        if isclose(pivot_val, 0.0, abs_tol = self.tolerance):
            return
        
        factor = self.matriz[target_r][pivot_c] / pivot_val
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
        """Devuelve fila con |A[row,col]| máximo desde start_row; -1 si la columna ~ 0."""
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
        Triangulación superior: pone 0 debajo de cada pivote y registra pasos.
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

            # Eliminar hacia abajo en la columna actual
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
        RREF: pivotes a 1 y ceros arriba de cada pivote (se recorre de abajo a arriba).
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
        """Ejecuta forward + backward (RREF) con registro de pasos."""
        self.frame = {}
        self.forward_elimination()
        self.backward_elimination_and_normalize()
        return self.frame

    # ----------------------
    # Análisis y solución
    # ----------------------
    def analyze(self) -> Dict[str, Any]:
        """Analiza [A|b] con analyze_argumented: rank, pivotes, básicas/libres, inconsistencias."""
        return analyze_argumented(self.matriz, tol=self.tolerance)

    def solve_and_log(self) -> Dict[str, Any]:
        """
        Registra el resumen del tipo de solución y devuelve un dict con
        'status', 'solution' (particular), 'basic_vars', 'free_vars', etc.
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
    
    # Cambios nuevos Sistemas homogeneos/ No homogeneos || Dependientes y no dependientes.
    
            # Verificación de dependencia lineal
        rank_A = info.get("rank_A", info.get("rank", 0))
        n_vars = self.columnas - 1
        dependent = rank_A < min(self.filas, n_vars)
        dep_msg = "Las filas de A son linealmente dependientes." if dependent else "Las filas de A son linealmente independientes."
        log_step(self.frame, dep_msg, self.matriz, det=None, tag="dependency_check")

        # Análisis combinado (homogeneidad + tipo de solución)
        if self.is_homogeneous:
            if status == "unique":
                log_step(self.frame, "Sistema homogéneo con única solución trivial (x = 0).", self.matriz, det=None, tag="homogeneous_unique")
            elif status == "infinite":
                log_step(self.frame, "Sistema homogéneo con infinitas soluciones (existen vectores no triviales en el núcleo).", self.matriz, det=None, tag="homogeneous_infinite")
        else:
            if status == "infinite":
                log_step(self.frame, "Sistema no homogéneo con infinitas soluciones (dependencia entre ecuaciones).", self.matriz, det=None, tag="nonhom_infinite")


    # ----------------------
    # Chequeos útiles
    # ----------------------
    def is_singular(self) -> Optional[bool]:
        """
        Devuelve True si rank(A) < n (A singular) para matrices cuadradas.
        None si A no es cuadrada.
        """
        # n = columnas de coeficientes
        n = self.columnas - 1
        m = self.filas
        if n != m:
            return None  # no aplica (A no es cuadrada)
        info = self.analyze()
        return info.get("rank", 0) < n
        
# -------- Runner --------
def run_gauss_jordan() -> None:
    """Runner interactivo: pide A y b, ejecuta Gauss–Jordan y muestra proceso + resumen."""
    rows, cols = inputs_matrix()
    matriz, vector = Matrix.make_equation(rows, cols)

    # Mostrar sistema ingresado (formato algebraico)
    print(print_equation(matriz, vector))

    # Ejecutar Gauss-Jordan con logs
    gj = GaussJordanMethod(matriz, vector)
    gj.run()
    results = gj.solve_and_log()

    # Imprimir proceso y resumen
    print_frame(gj.frame)
    print(print_equation(matriz, vector))
    print_summary(results)

__all__ = ["GaussJordanMethod", "run_gauss_jordan"]