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
- core.matrix.Matrix (para estructura y pretty-print de matriz)
- utils.printMethods (log_step)
- core.system_solver.gauss_solver (analyze_argumented, solve_from_upper)

El runner interactivo vive en cli.method_runners; aquí no se imprime nada.
"""

from __future__ import annotations
import copy
from typing import Any, Dict, List, Optional, Tuple
from math import isclose 
from core.matrix import Matrix
from core.system_solver.gauss_solver import analyze_argumented, solve_from_upper
from utils.EquationFunctions import format_number
from utils.printMethods import log_step, print_parametric_solution_from_rref
from core.matrix_tools import determinant, is_singular

def _una_linea(texto: str) -> str:
    """Aplana un texto multilínea para usarlo como paso del frame.

    log_step usa la descripción como clave del dict, y print_frame /
    frame_to_html la pintan en una sola línea; la forma paramétrica viene en
    dos (la expresión y la declaración de parámetros).
    """
    return " · ".join(parte.strip() for parte in texto.splitlines() if parte.strip())


class GaussJordanMethod(Matrix):
    """
    Implementación de Gauss–Jordan sobre [A | b].

    - Forward: triangulación superior (ceros debajo de pivotes).
    - Backward + normalize: RREF (pivotes = 1 y ceros arriba/abajo).
    - Registro de operaciones y análisis del sistema.

    Uso típico:
        A, b = make_equation(m, n)   # cli.inputsmatrix, o cualquier fuente de datos
        gj = GaussJordanMethod(A, b)
        gj.run()                 # RREF con logs
        result = gj.solve_and_log()
    """
    
    def __init__(self, matriz: List[List[float]], b: Optional[List[float]]) -> None:
        if b is None:
            raise ValueError("GaussJordanMethod requiere A y b.")
        
        if len(b) != len(matriz):
            raise ValueError("El vector b debe tener la misma cantidad de filas que A.")

        # Validaciones de forma y tipo (rama Sistemas). Van antes de construir la
        # aumentada a propósito: el list(map(float, ...)) de abajo ya reventaría
        # con un ValueError/TypeError genérico de float(), y estas comprobaciones
        # quedarían inalcanzables. Aquí sí dan un mensaje que dice qué pasa.
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
        # Determina si el sistema es homogéneo (todos los valores de b son 0)
        self.is_homogeneous = all(isclose(bi, 0.0, abs_tol=self.tolerance) for bi in self.b)


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
        # Tipo de sistema como primer paso del registro (rama Sistemas). Va aquí y
        # no en __init__ porque la línea de arriba vacía el frame: registrarlo en
        # el constructor, como venía en la rama, lo dejaba siempre fuera del log.
        msg = "Sistema homogéneo (b = 0)" if self.is_homogeneous else "Sistema no homogéneo (b ≠ 0)"
        log_step(self.frame, msg, self.matriz, det=None, tag="homogeneity_check")
        # Calcular determinante de A (si es cuadrada) usando Gauss-Jordan y registrar
        try:
            det = determinant(self.A, tol=self.tolerance)
            self.determinante = det
            log_step(self.frame, f"Determinante de A = {format_number(det)}", self.matriz, det=det, tag="det")
            sing = self.is_singular()
            sing_msg = "singular" if sing else "no singular" if sing is not None else "no aplicable"
            log_step(self.frame, f"Estado de singularidad: {sing_msg}", self.matriz, det=det, tag="singularity")
        except Exception:
            # si no es cuadrada o falla, no interrumpimos el proceso
            pass
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
        # Detección explícita de homogeneidad y dependencia lineal en el resumen
        tipo_sistema = "homogéneo" if self.is_homogeneous else "no homogéneo"
        # 'rank' sale de find_pivots_from_upper, que sólo escanea las columnas de
        # coeficientes (range(n)), así que ya es rank(A) y no el de la aumentada.
        # La clave "rank_A" que se consultaba antes no existe en ese dict.
        rank_A = info.get("rank", 0)
        n_vars = self.columnas - 1
        # Dependencia de FILAS: las m filas de A son dependientes sii rank(A) < m.
        # El criterio anterior, rank < min(filas, n_vars), fallaba con más filas
        # que columnas: una 3x2 de rango 2 daba "independiente", cuando 3 vectores
        # en R² son necesariamente dependientes.
        dependent = rank_A < self.filas
        dependencia = "dependiente" if dependent else "independiente"
        log_step(self.frame, f"Resumen: Tipo de solución = {status} | Sistema {tipo_sistema} | Filas de A {dependencia}", self.matriz, det=None, tag="summary")

        if status == "inconsistent":
            log_step(self.frame, "Sistema inconsistente: no existe solución", self.matriz, det=None, tag="inconsistent")
            return {**info, "solution": None}

        # Solución particular y paramétrica
        result = solve_from_upper(self.matriz, pivots=pivots, tol=self.tolerance)
        sol = result.get("solution")
        basic = result.get("basic_vars", [])
        free = result.get("free_vars", [])
        # Forma paramétrica (B3). Antes se leía result["parametric_solution"], una
        # clave que solve_from_upper() nunca devuelve, así que `parametric` era
        # siempre None y los bloques `if parametric:` de abajo eran código muerto.
        # self.matriz ya está en RREF cuando se llega aquí (run() corrió antes),
        # que es justo lo que print_parametric_solution_from_rref espera.
        # Sólo tiene sentido con variables libres; con solución única la función
        # devolvería el listado de valores, que ya se registra como "solution".
        parametric = None
        if status == "infinite":
            parametric = print_parametric_solution_from_rref(self.matriz, tol=self.tolerance)

        # Log incondicional de la solución particular. Estaba en main y en la rama
        # Vectores, y se perdió al integrar HomoNohomo, que lo repartió entre las
        # ramas de análisis: para status == "infinite" la única vía que quedaba era
        # el bloque `if parametric:`, que nunca se ejecuta (B3). Se restaura aquí
        # para no registrar menos que antes.
        if sol is not None:
            sol_str = [format_number(v) for v in sol]
            log_step(self.frame, f"Solución particular (libres=0): [{', '.join(sol_str)}]", self.matriz, det=None, tag="solution")

        def idxs_to_vars(idxs): return "None" if not idxs else ", ".join(f"x{(i+1)}" for i in idxs)
        log_step(self.frame, f"Variables básicas: {idxs_to_vars(basic)} | Variables libres: {idxs_to_vars(free)}", self.matriz, det=None, tag="vars")

        dep_msg = "Las filas de A son linealmente dependientes." if dependent else "Las filas de A son linealmente independientes."
        log_step(self.frame, dep_msg, self.matriz, det=None, tag="dependency_check")

        # Análisis combinado (homogeneidad + tipo de solución)
        if self.is_homogeneous:
            if status == "unique":
                log_step(self.frame, "Sistema homogéneo con única solución trivial (x = 0).", self.matriz, det=None, tag="homogeneous_unique")
                if sol is not None:
                    sol_str = [format_number(v) for v in sol]
                    log_step(self.frame, f"Solución trivial: [{', '.join(sol_str)}]", self.matriz, det=None, tag="trivial_solution")
            elif status == "infinite":
                log_step(self.frame, "Sistema homogéneo con infinitas soluciones (existen vectores no triviales en el núcleo).", self.matriz, det=None, tag="homogeneous_infinite")
                if parametric:
                    log_step(self.frame, f"Solución paramétrica (no trivial): {_una_linea(parametric)}", self.matriz, det=None, tag="parametric_solution")
        else:
            if status == "unique":
                if sol is not None:
                    sol_str = [format_number(v) for v in sol]
                    # Solución particular + no trivial
                    log_step(self.frame, f"Solución particular + no trivial: [{', '.join(sol_str)}]", self.matriz, det=None, tag="particular_solution")
            elif status == "infinite":
                log_step(self.frame, "Sistema no homogéneo con infinitas soluciones (dependencia entre ecuaciones).", self.matriz, det=None, tag="nonhom_infinite")
                # Solución general con variables libres simbólicas.
                # print_parametric_solution_from_rref ya nombra las libres s1, s2, …
                # y las básicas x₁, x₂, …; el .replace("x", "s") que había aquí
                # convertía también las básicas en s₁ y corrompía la expresión.
                if parametric:
                    log_step(self.frame, f"Solución general (paramétrica): {_una_linea(parametric)}", self.matriz, det=None, tag="parametric_solution")

        # Conclusión final sobre el sistema
        conclusion = f"Conclusión: El sistema es {tipo_sistema}, las filas de A son {dependencia}, rango(A) = {rank_A}. "
        if self.is_homogeneous:
            if status == "unique":
                conclusion += f"Ax=0 con rango A = n -> única solución trivial."
            elif status == "infinite":
                conclusion += f"Ax=0 con rango A < n -> infinitas soluciones (no triviales)."
        else:
            if status == "unique":
                conclusion += f"Ax=b con rango A = n -> única solución particular (no trivial)."
            elif status == "infinite":
                conclusion += f"Ax=b con rango A < n -> infinitas soluciones generales (paramétricas)."
        log_step(self.frame, conclusion, self.matriz, det=None, tag="conclusion")

        return {**result,
            "parametric_solution": parametric,
            "tipo_sistema": tipo_sistema,
            "dependencia": dependencia,
            "determinant": self.determinante,
            "is_singular": self.is_singular()
           }

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

__all__ = ["GaussJordanMethod"]
