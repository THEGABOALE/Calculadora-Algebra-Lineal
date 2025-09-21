from .matrix import Matrix
from math import isclose
import copy
from typing import Any, Dict, List, Optional, Tuple
from .system_solver.gauss_solver import solve_from_upper, analyze_argumented

"""
Metodo de Gauss con:
    - Soporte para matrices rectangulares (m x n).
    - Calculo de determinante SOLO si la matriz es cuadrada.
    - Registro de pasos estandarizado en self.frame (dict de pasos -> {matrix, det, tag}).
    - Métodos de impresión del proceso: print_process() y run_and_print().
"""
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
    
    # ----------------------
    # MÉTODO PRINCIPAL
    # ----------------------
    def gauss_method(self) -> dict[str, dict[str, any]]:
        self.frame = {}
        self.determinante = 1.0
        
        max_steps = min(self.filas, self.columnas)
        if self.filas == self.columnas and self.null_determinant():
            return self.frame
        
        if not self.null_determinant():
            for col in range(max_steps):
                self.pivote(col)
                self.triangular_reduction(col)
            if self.filas == self.columnas:
                self.determinant_result()
        return self.frame

    # ----------------------
    # ELIMINACION HACIA ADELANTE PARA MATRIZ AUMENTADA
    # ----------------------
    def fordward_elimination_aug(self) -> Tuple[List[List[float]], List[Tuple[int,int]]]:
        """Orquesta la eliminación hacia adelante sobre la matriz aumentada self.matriz.
        - Usa pivot parcial por filas (no intercambia columnas).
        - Reutiliza triangular_reduction(col) para eliminar por debajo del pivote.
        - Registra pasos en self.frame mediante log_step.
        - Al final actualiza self.matriz, self.pivots y dimensiones.
        """
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
        
        for col in range(n):
            if row >= m:break
            
            # Usar pivote parcial
            sel = max(range(row,m),key=lambda r: abs(aug[r][col]))
            if isclose(aug[sel][col], 0.0, abs_tol=self.tolerance):
                continue
            
            # Swap filas si es necesario
            if sel != row:
                self.swipe_rows(row, sel)
                
            # Registrar pivote
            pivots.append((row, col))
            pivot_val = aug[row][col]
            
            for r in range(row +1, m):
                if isclose(aug[r][col],0.0,abs_tol=self.tolerance):
                    continue
                factor = aug[r][col] / pivot_val
                for c in range(col, n+1):
                    aug[r][c] -= factor * aug[row][c]
                    if isclose(aug[r][c],0.0,abs_tol=self.tolerance):
                        aug[r][c] =0.0
            row +=1
        
        self.matriz = aug
        self.filas = len(aug)
        self.columnas = len(aug[0]) if aug else 0
        self.pivots = pivots
        
        return self.matriz, pivots

    # ----------------------
    # solve_and_log: ejecuta eliminación, resuelve y registra resumen (llamen a dio)
    # ----------------------
    def solve_and_log(self) -> Dict[str, Any]:
        """
        Registra un resumen final en self.frame, devolviendo el dict 
        resultado de solve_from_upper
        """
        if not getattr(self, "is_augmented", False):
            raise RuntimeError("La instancia no contiene una matriz aumentada")
        
        self.fordward_elimination_aug()
        result = solve_from_upper(self.matriz, pivots=self.pivots)
        
        status = result.get('status')
        sol = result.get('solution')
        basic = result.get('basic_vars',[])
        free = result.get('free_vars',[])
        
        return result


    # ----------------------
    # CHEQUEOS DE SINGULARIDAD (solo para cuadradas)
    # ----------------------
    def null_determinant(self) -> bool:
        if self.filas != self.columnas:
            return False
        
        # Validar Matrices singulares por lineas o columnas 0
        for row in range(self.filas):
            if all(self.matriz[row][i]==0 for i in range(self.columnas)):
                return True
            
        for col in range(self.columnas):
            if all(self.matriz[i][col]==0 for i in range(self.filas)):
                return True
            
        # Validar Matrices singulares por repeticion de filas o columnas
        for i in range(self.filas):
            for j in range(i+1, self.filas):
                if self.matriz[i] == self.matriz[j]:
                    return True
                
        for i in range(self.columnas):
            for j in range(i+1, self.columnas):
                col_i = [self.matriz[k][i] for k in range(self.filas)]
                col_j = [self.matriz[k][j] for k in range(self.filas)]
                if col_i == col_j:
                    return True
        
        return False
    
    
    # ----------------------
    # DETERMINANTE 
    # ----------------------
    def determinant_result(self):
        if self.filas != self.columnas:
            return 
        
        diag_product = 1.0
        limit = min(self.filas, self.columnas)
        for i in range(limit):
            diag_product *= self.matriz[i][i]
            
        final_dect = self.determinante * diag_product


    # ---------------------
    # OPERACIONES ELEMENTALES
    # ----------------------
    def swipe_rows(self, fila_a, fila_b) -> None:
        """
        Intercambia las filas de la matriz, actualiza el determinante y
        guarda el estado en self.frame
        """
        temp = self.matriz[fila_a]
        self.matriz[fila_a] = self.matriz[fila_b]
        self.matriz[fila_b] = temp
        # Cambiar el signo del determinante
        if self.filas == self.columnas:
            self.determinante *= -1.0

        
    def swipe_col(self, col_a, col_b) -> None:
        """
        Intercambia las columnas de la matriz, actualiza el determinante
        y guarda el estado en self.frame
        """
        for fila in range(self.filas):
            temp = self.matriz[fila][col_a]
            self.matriz[fila][col_a] = self.matriz[fila][col_b]
            self.matriz[fila][col_b] = temp
            
        # Cambiar el determinante
        if self.filas == self.columnas:
            self.determinante *= -1.0
    
    
    def triangular_reduction(self, col):
        if col >= self.filas or col >= self.columnas:
            return
        
        pivote = self.matriz[col][col]
        if isclose(pivote, 0.0, abs_tol=self.tolerance):
            return
        
        for fila in range(col + 1, self.filas):
            valor_actual = self.matriz[fila][col]
            if isclose(valor_actual, 0.0, abs_tol=self.tolerance):
                continue
            
            factor = valor_actual / pivote
            nueva_fila = []
            for i in range(self.columnas):
                nuevo_valor = self.matriz[fila][i] - factor * self.matriz[col][i]
                if isclose(nuevo_valor, 0.0, abs_tol=self.tolerance):
                    nuevo_valor = 0.0
                nueva_fila.append(nuevo_valor)
            self.matriz[fila] = nueva_fila
            
    
    def pivote(self, col:int):
        """
        Busca el mejor pivote en la columna 'col' (valor más cercano a 1 y distinto de 0).
        Si no lo encuentra en la columna, busca en otras columnas de la misma fila.
        Realiza el intercambio de filas o columnas si es necesario.
        Guarda el paso en self.frame si no hay pivote.
        """
        if col >= self.filas or col >= self.columnas:
            return
        
        row_option = -1
        col_option = col
        distance_option = float('inf')
        
        for fila in range(col, self.filas):
            valor = self.matriz[fila][col]
            if isclose(valor, 0.0, abs_tol=self.tolerance):
                continue
            distance = abs(valor -1.0)
            if isclose(valor, 1.0, abs_tol=self.tolerance):
                row_option = fila
                distance_option = 0.0
                break
            elif distance < distance_option:
                distance_option = distance
                row_option = fila
                
        if row_option != -1 and not isclose(self.matriz[row_option][col], 1.0, abs_tol=self.tolerance):
            for col_alt in range(col+1, self.columnas):
                valor = self.matriz[col][col_alt]
                if isclose(valor, 0.0, abs_tol=self.tolerance):
                    continue
                distance = abs(valor-1.0)
                if isclose(valor, 1.0, abs_tol=self.tolerance):
                    col_option = col_alt
                    distance_option = 0.0
                    break
                elif distance < distance_option:
                    distance_option = distance
                    col_option = col_alt
                    
        if row_option == -1:
            return
        
        if col_option != col:
            self.swipe_col(col, col_option)
            return
        
        if row_option != col:
            self.swipe_rows(col, row_option)
            return
