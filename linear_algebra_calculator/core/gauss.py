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

Criterio de "es cero": el de core/matrix_tools.py (cota de redondeo por
entrada, ver documentation/CriterioNumerico.md), llevado en paralelo con
CotasDeRedondeo. La eliminación deja el ruido en 0.0 exacto y
solve_from_upper analiza la matriz sin umbral propio. Antes era 1e-13
absoluto.

La eliminación SIEMPRE se completa. Antes, si [A|b] era cuadrada (A de
m×(m-1)) y tenía una fila/columna nula o dos filas/columnas iguales, se
cortaba antes de eliminar y el análisis leía la matriz sin reducir: un
sistema 3×2 con dos ecuaciones repetidas y solución única salía
"infinitas". Una matriz singular no dice si el sistema es incompatible o
indeterminado; eso sólo lo dice la eliminación completa.

Dependencias (internas)
- core.matrix.Matrix
- core.matrix_tools (CotasDeRedondeo)
- core.system_solver.gauss_solver (analyze_argumented, solve_from_upper)
- utils.printMethods (log_step)

El runner interactivo vive en cli.method_runners; aquí no se imprime nada.
"""

from core.matrix import Matrix
import copy
import math
from typing import Any, Dict, List, Optional, Tuple

from core.matrix_tools import CotasDeRedondeo, producto_sin_desborde, restar_multiplo_de_fila
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
        # det(A) cuando A es cuadrada (se llena en gauss_method); None si no.
        self.determinante: Optional[float] = None
        # Se conserva por compatibilidad; ya no decide nada (ver CotasDeRedondeo).
        self.tolerance = 1e-13 # Notacion cientifica
        self.frame: List[Dict[str, Any]] = []
        self.pivots: List[Tuple[int,int]] = []
        self.analize: Dict[str, Any] = {}
        self._cotas: Optional[CotasDeRedondeo] = None
        self._signo: float = 1.0

    # ----------------------
    # Forma de A (no de [A|b])
    # ----------------------
    def _n_incognitas(self) -> int:
        return self.columnas - 1 if self.is_augmented else self.columnas

    def _a_es_cuadrada(self) -> bool:
        """A es n×n. Antes se comparaba filas == columnas de la AUMENTADA,
        que es m×(n+1): para un sistema cuadrado nunca se cumplía, y sí para
        A de m×(m-1)."""
        return self.filas == self._n_incognitas()

    # ----------------------
    # Eliminación hacia adelante (única, compartida)
    # ----------------------
    def _eliminar_hacia_adelante(self) -> List[Tuple[int, int]]:
        aug = self.matriz
        m = len(aug)
        if m == 0:
            self.pivots = []
            return []
        n = len(aug[0]) - 1
        self._cotas = CotasDeRedondeo(aug)
        cotas = self._cotas
        row = 0
        pivots: List[Tuple[int,int]] = []
        for col in range(n):
            if row >= m:
                break
            candidatos = [r for r in range(row, m)
                          if aug[r][col] != 0.0 and not cotas.es_cero(aug[r][col], r, col)]
            if not candidatos:
                # Lo que quede en la columna es ruido de redondeo: 0 exacto.
                for r in range(row, m):
                    aug[r][col] = 0.0
                log_step(self.frame, f"No hay pivote significativo en la columna {col+1}", aug, det=None, tag="no_pivot")
                continue
            sel = max(candidatos, key=lambda r: abs(aug[r][col]))
            if sel != row:
                self.swipe_rows(row, sel)
            pivots.append((row, col))
            pivot_val = aug[row][col]
            log_step(self.frame, f"Pivote en A[{row+1},{col+1}] = {format_number(pivot_val)}", aug, det=None, tag="pivot")
            for r in range(row + 1, m):
                if aug[r][col] == 0.0:
                    continue
                if cotas.es_cero(aug[r][col], r, col):
                    aug[r][col] = 0.0
                    continue
                entrada = aug[r][col]
                factor = restar_multiplo_de_fila(aug, cotas, r, row, entrada, pivot_val, desde=col)
                aug[r][col] = 0.0
                for c in range(col + 1, n + 1):
                    if cotas.es_cero(aug[r][c], r, c):
                        aug[r][c] = 0.0
                # Si el multiplicador no es representable (1e-300/1e300), se
                # muestra como cociente: es el que se aplicó, término a término.
                texto_factor = format_number(factor) if factor is not None else \
                    f"{format_number(entrada)}/{format_number(pivot_val)}"
                log_step(self.frame, f"F{r+1} -> F{r+1} - ({texto_factor})*F{row+1}", aug, det=None, tag="elim")
            row += 1
        self.matriz = aug
        self.filas = len(aug)
        self.columnas = len(aug[0]) if aug else 0
        self.pivots = pivots
        return pivots

    def gauss_method(self) -> List[Dict[str, Any]]:
        # Unifica el registro de pasos y la lógica de resolución, como en Gauss-Jordan
        self.frame = []
        self.determinante = None
        self._signo = 1.0
        if not getattr(self, "is_augmented", False):
            raise RuntimeError("La instancia no contiene una matriz aumentada")
        if len(self.matriz) == 0:
            return self.frame
        log_step(self.frame, "Matriz aumentada inicial", self.matriz, det=None, tag="start")
        # Atajos de singularidad sobre A: se registran como observación, pero
        # NO cortan el procedimiento (ver el docstring del módulo).
        if self._a_es_cuadrada():
            self.null_determinant()
        self._eliminar_hacia_adelante()
        log_step(self.frame, "Matriz aumentada triangular superior (U)", self.matriz, det=None, tag="upper")
        if self._a_es_cuadrada():
            self.determinant_result()
        return self.frame

    def fordward_elimination_aug(self) -> Tuple[List[List[float]], List[Tuple[int,int]]]:
        # Antes era una copia de la eliminación de gauss_method con sus propias
        # reglas; ahora es la misma eliminación, sin los pasos de determinante.
        if not getattr(self, "is_augmented", False):
            raise RuntimeError("La instancia no contiene una matriz aumentada")
        if len(self.matriz) == 0:
            return self.matriz, []
        self._signo = 1.0
        log_step(self.frame, "Matriz aumentada inicial", self.matriz, det=None, tag="start")
        pivots = self._eliminar_hacia_adelante()
        log_step(self.frame, "Matriz aumentada triangular superior (U)", self.matriz, det=None, tag="upper")
        return self.matriz, pivots

    def solve_and_log(self) -> Dict[str, Any]:
        # Solo analiza y resume, asume que gauss_method ya fue ejecutado. Sin
        # tolerancia: la eliminación ya dejó el ruido en 0.0 exacto.
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
        """Atajos de singularidad sobre A (no sobre [A|b]): una fila o columna
        nula, o dos filas o columnas iguales, implican det(A) = 0.

        Sólo registra la observación y devuelve True/False: NO decide el tipo
        de sistema. Con A singular el sistema puede ser incompatible o tener
        infinitas soluciones, y eso lo distingue la eliminación, que sigue.
        Comparación exacta: son datos de entrada, no resultados de cuentas.
        """
        if not self._a_es_cuadrada():
            return False
        n = self._n_incognitas()
        A = [fila[:n] for fila in self.matriz]
        sigue = " No hay solución única; la eliminación continúa para distinguir infinitas soluciones de sistema incompatible."
        for row in range(n):
            if all(A[row][i] == 0 for i in range(n)):
                log_step(self.frame, f"Fila {row+1} de A es nula: det(A) = 0 (A singular).{sigue}", self.matriz, det=0, tag="singular")
                return True
        for col in range(n):
            if all(A[i][col] == 0 for i in range(n)):
                log_step(self.frame, f"Columna {col+1} de A es nula: det(A) = 0 (A singular).{sigue}", self.matriz, det=0, tag="singular")
                return True
        for i in range(n):
            for j in range(i+1, n):
                if A[i] == A[j]:
                    log_step(self.frame, f"Filas {i+1} y {j+1} de A son iguales: det(A) = 0 (A singular).{sigue}", self.matriz, det=0, tag="singular")
                    return True
        for i in range(n):
            for j in range(i+1, n):
                if [A[k][i] for k in range(n)] == [A[k][j] for k in range(n)]:
                    log_step(self.frame, f"Columnas {i+1} y {j+1} de A son iguales: det(A) = 0 (A singular).{sigue}", self.matriz, det=0, tag="singular")
                    return True
        return False

    def determinant_result(self):
        """det(A) = (signo de los intercambios) · producto de la diagonal de U.

        Sólo para A cuadrada (antes se calculaba sobre la diagonal de la
        aumentada cuando ESA era cuadrada, es decir, para A de m×(m-1), y
        nunca para un sistema cuadrado). Si A es singular, la última fila de
        la parte A de U es nula y el producto es 0.
        """
        if not self._a_es_cuadrada():
            return
        n = self._n_incognitas()
        diagonal = [self.matriz[i][i] for i in range(n)]
        singular = any(d == 0.0 for d in diagonal)
        # producto_sin_desborde (el mismo que usa matrix_tools.determinant):
        # math.prod multiplicaba de a uno y diag(1e-200, 1e-200, 1e300) daba
        # 0 -- con un paso que decía "no representable" de un det = 1e-100
        # que sí lo es. Ahora 0.0 / inf sólo aparecen si el RESULTADO no
        # entra en un double.
        det = 0.0 if singular else producto_sin_desborde(diagonal, self._signo)
        if det == 0:
            det = 0.0           # sin -0.0
        self.determinante = det
        factores = "".join(f"({format_number(d)})" for d in diagonal)
        signo = "" if self._signo > 0 else "−"
        texto = f"Determinante de A = {signo}{factores} = {format_number(det)}"
        if not singular and det == 0.0:
            texto += " (|det(A)| < ~5e-324: no representable en coma flotante, subdesborda; A es invertible)"
        elif math.isinf(det):
            texto += " (|det(A)| > ~1.8e308: no representable en coma flotante, desborda)"
        log_step(self.frame, texto, self.matriz, det=format_number(det), tag="det")

    def swipe_rows(self, fila_a, fila_b) -> None:
        temp = self.matriz[fila_a]
        self.matriz[fila_a] = self.matriz[fila_b]
        self.matriz[fila_b] = temp
        if self._cotas is not None:
            self._cotas.intercambiar(fila_a, fila_b)
        texto = f"Fila {fila_a+1} <-> Fila {fila_b+1}"
        if self._a_es_cuadrada():
            self._signo *= -1.0
            texto += " (cambia el signo de det(A))"
        log_step(self.frame, texto, self.matriz, det=None, tag="swap_rows")

__all__ = ['GaussMethod']
