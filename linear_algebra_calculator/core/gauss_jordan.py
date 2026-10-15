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
- Criterio de "es cero": el de core/matrix_tools.py (cota de redondeo por
  entrada, ver documentation/CriterioNumerico.md), llevado en paralelo con
  CotasDeRedondeo. La eliminación deja el ruido en 0.0 exacto, así que el
  análisis posterior no usa ningún umbral propio. Antes se usaba 1e-12
  absoluto: con coeficientes ~1e-13 no había pivotes ("infinitas" para un
  sistema invertible) y con coeficientes ~1e8 el ruido pasaba por dato
  ("incompatible" para un sistema compatible).

Entradas
- A: list[list[float]]     b: list[float] (len(b) == filas(A))

Dependencias (internas)
- core.matrix.Matrix (para estructura y pretty-print de matriz)
- utils.printMethods (log_step)
- core.system_solver.gauss_solver (analyze_argumented, solve_from_upper)

El runner interactivo vive en cli.method_runners; aquí no se imprime nada.
"""

from __future__ import annotations
import math
import warnings
import copy
from typing import Any, Dict, List, Optional, Tuple
from core.matrix import Matrix
from core.system_solver.gauss_solver import analyze_argumented, solve_from_upper
from utils.EquationFunctions import format_number
from utils.printMethods import log_step, print_parametric_solution_from_rref
from core.matrix_tools import CotasDeRedondeo, determinant, restar_multiplo_de_fila
# Singularidad de A sobre la matriz de coeficientes ORIGINAL (rango por el
# criterio de matrix_tools). Alias para no confundirla con el método
# GaussJordanMethod.is_singular().
from core.matrix_tools import is_singular as singular_por_rango

def _una_linea(texto: str) -> str:
    """Aplana un texto multilínea para usarlo como paso del frame.

    Cada paso del frame es una sola línea de texto (print_frame en el CLI, o
    los adaptadores de la API, la pintan así); la forma paramétrica viene en
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
        
        # Log y tolerancias. `tolerance` se conserva como atributo por
        # compatibilidad, pero ya no decide nada: "es cero" lo decide
        # self._cotas (criterio de core/matrix_tools.py).
        self.tolerance: float = 1e-12
        self.frame: List[Dict[str, Any]] = []
        self.pivots: List[Tuple[int, int]] = []   # lista de (fila, col) de pivotes detectados en forward
        self._cotas: Optional[CotasDeRedondeo] = None
        # True cuando self.matriz ya está escalonada (forward_elimination corrió):
        # recién ahí analyze() puede leer el rango de la matriz.
        self._eliminada: bool = False

        # Determinante: solo relevante si A es cuadrada y no escalamos (aquí se escala para RREF),
        # así que lo mantenemos informativo (no lo reportamos).
        self.determinante: Optional[float] = None
        # Homogéneo: b = 0 EXACTO. b es dato, no resultado de una cuenta: un
        # b_i = 1e-13 tipeado es distinto de cero (antes, con |b_i| <= 1e-12,
        # el sistema se declaraba homogéneo).
        self.is_homogeneous = all(bi == 0 for bi in self.b)

    # ----------------------
    # Helpers numéricos
    # ----------------------
    def _cotas_actuales(self) -> CotasDeRedondeo:
        if self._cotas is None:
            self._cotas = CotasDeRedondeo(self.matriz)
        return self._cotas

    # ----------------------
    # Operaciones elementales (con log)
    # ----------------------
    def _swap_rows(self, r1: int, r2: int) -> None:
        """Intercambia filas y registra el paso (no cambia determinante aquí)."""
        if r1 == r2:
            return
        self.matriz[r1], self.matriz[r2] = self.matriz[r2], self.matriz[r1]
        self._cotas_actuales().intercambiar(r1, r2)
        log_step(self.frame, f"F{r1+1} <-> F{r2+1}", self.matriz, det=None, tag="swap_rows")
        
    def _scale_row(self, r: int, factor: float) -> None:
        """Normaliza fila: F_r := F_r / factor (factor ≠ 0).

        Se saltea sólo si factor es 1 exacto: antes se salteaba con
        |factor - 1| <= 1e-12 y el pivote quedaba sin normalizar.
        """
        if factor == 1.0:
            return
        if factor == 0.0:
            raise ValueError("No se puede escalar por 0.")
        self.matriz[r] = [v / factor for v in self.matriz[r]]
        self._cotas_actuales().escalar(r, factor)
        log_step(self.frame, f"F{r+1} -> F{r+1} / {format_number(factor)}", self.matriz, det=None, tag="scale")
        
    def _row_elim(self, target_r: int, pivot_r: int, pivot_c: int) -> None:
        """
        Eliminación en columna pivot_c:
            F_target := F_target - (A[target,pivot_c]/A[pivot_r,pivot_c]) * F_pivot
        """
        cotas = self._cotas_actuales()
        pivot_val = self.matriz[pivot_r][pivot_c]
        if pivot_val == 0.0:
            return

        entrada = self.matriz[target_r][pivot_c]
        if entrada == 0.0:
            return
        if cotas.es_cero(entrada, target_r, pivot_c):
            # Ruido de redondeo, no un coeficiente: se deja en 0 exacto, sin
            # registrar una operación que no hace nada.
            self.matriz[target_r][pivot_c] = 0.0
            return

        row_len = len(self.matriz[0])
        factor = restar_multiplo_de_fila(self.matriz, cotas, target_r, pivot_r, entrada, pivot_val, desde=pivot_c)
        self.matriz[target_r][pivot_c] = 0.0
        for j in range(pivot_c + 1, row_len):
            if cotas.es_cero(self.matriz[target_r][j], target_r, j):
                self.matriz[target_r][j] = 0.0

        negativo = (entrada < 0) != (pivot_val < 0)
        signo = "+" if negativo else "-"
        # Multiplicador no representable (1e-300/1e300): se muestra como cociente.
        magnitud = format_number(abs(factor)) if factor is not None else \
            f"({format_number(abs(entrada))}/{format_number(abs(pivot_val))})"
        log_step(self.frame,
                 f"F{target_r+1} -> F{target_r+1} {signo} {magnitud}*F{pivot_r+1}",
                 self.matriz, det=None, tag="elim")
        
    # ----------------------
    # Pivoteo parcial por filas
    # ----------------------
    def _select_pivot_row(self, start_row: int, col: int) -> int:
        """Devuelve la fila con |A[row,col]| máximo desde start_row, entre las
        entradas que no son cero según el criterio; -1 si no hay ninguna (lo
        que queda en la columna es ruido y se deja en 0 exacto)."""
        cotas = self._cotas_actuales()
        candidatos = [r for r in range(start_row, self.filas)
                      if self.matriz[r][col] != 0.0 and not cotas.es_cero(self.matriz[r][col], r, col)]
        if not candidatos:
            for r in range(start_row, self.filas):
                self.matriz[r][col] = 0.0
            return -1
        return max(candidatos, key=lambda r: abs(self.matriz[r][col]))
    
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
        self._cotas = CotasDeRedondeo(self.matriz)

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
        self._eliminada = True
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
            if piv == 0.0:
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
    def run(self) -> List[Dict[str, Any]]:
        """Ejecuta forward + backward (RREF) con registro de pasos."""
        self.frame = []
        # Tipo de sistema como primer paso del registro (rama Sistemas). Va aquí y
        # no en __init__ porque la línea de arriba vacía el frame: registrarlo en
        # el constructor, como venía en la rama, lo dejaba siempre fuera del log.
        msg = "Sistema homogéneo (b = 0)" if self.is_homogeneous else "Sistema no homogéneo (b ≠ 0)"
        log_step(self.frame, msg, self.matriz, det=None, tag="homogeneity_check")
        # Calcular determinante de A (si es cuadrada) usando Gauss-Jordan y registrar
        try:
            # Sin tol: criterio de cero por cota de redondeo de matrix_tools. Con
            # el 1e-12 absoluto de antes, det(1e-8·I) se mostraba como 0 en un
            # sistema que el propio Gauss-Jordan resolvia con solucion unica.
            with warnings.catch_warnings():
                # determinant() avisa con RuntimeWarning si |det(A)| no entra
                # en un double; acá se dice en el paso en vez de "det = 0".
                warnings.simplefilter("ignore", RuntimeWarning)
                det = determinant(self.A)
            self.determinante = det
            # Singularidad de A sobre A ORIGINAL. Antes se usaba
            # self.is_singular(), que miraba self.matriz con analyze_argumented
            # ANTES de eliminar: sin escalonar, cada fila no nula "tiene
            # pivote", y [[1,2],[2,4]] (rango 1) salía "no singular" justo
            # debajo de "Determinante de A = 0".
            sing = singular_por_rango(self.A)
            if (det == 0.0 or math.isinf(det)) and sing is False:
                log_step(self.frame,
                         "Determinante de A: no representable en coma flotante "
                         f"({'subdesborda a 0' if det == 0.0 else 'desborda a infinito'}); A es invertible",
                         self.matriz, det=None, tag="det")
            else:
                log_step(self.frame, f"Determinante de A = {format_number(det)}", self.matriz, det=det, tag="det")
            if sing is None:
                sing_msg = "no aplicable (A no es cuadrada)"
            elif sing:
                # Singular NO es incompatible: sólo dice que no hay solución
                # única. Compatible indeterminado o incompatible se decide al
                # eliminar (rango(A) frente a rango([A|b])).
                sing_msg = ("singular (rango(A) < n): no hay solución única; si Ax = b es compatible "
                            "(infinitas soluciones) o incompatible se decide al eliminar")
            else:
                sing_msg = "no singular (rango(A) = n): Ax = b tiene solución única"
            log_step(self.frame, f"Estado de singularidad de A: {sing_msg}", self.matriz, det=det, tag="singularity")
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
        """Analiza [A|b] con analyze_argumented: rank, pivotes, básicas/libres, inconsistencias.

        Sin tolerancia: la eliminación ya dejó el ruido en 0.0 exacto con el
        criterio de core/matrix_tools.py. Antes se volvía a mirar la matriz
        final con 1e-12 absoluto, que descartaba un b_i = 1e-13 real (0 = 1e-13
        salía "compatible").
        """
        return analyze_argumented(self.matriz)

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
            # Mismas claves que las otras ramas: antes faltaban is_singular,
            # determinant, tipo_sistema... y r["is_singular"] daba KeyError
            # justo en el caso incompatible.
            return {**info, "solution": None,
                    "parametric_solution": None,
                    "tipo_sistema": tipo_sistema,
                    "dependencia": dependencia,
                    "determinant": self.determinante,
                    "is_singular": self.is_singular()}

        # Solución particular y paramétrica
        result = solve_from_upper(self.matriz, pivots=pivots)
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
            parametric = print_parametric_solution_from_rref(self.matriz)

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

        Válido antes y después de eliminar: analyze() sólo sabe leer el rango
        de una matriz YA escalonada, así que antes de forward_elimination se
        usa core.matrix_tools.is_singular sobre A original (mismo criterio
        de cero que la eliminación).
        """
        # n = columnas de coeficientes
        n = self.columnas - 1
        m = self.filas
        if n != m:
            return None  # no aplica (A no es cuadrada)
        if not self._eliminada:
            return singular_por_rango(self.A)
        info = self.analyze()
        return info.get("rank", 0) < n

__all__ = ["GaussJordanMethod"]
