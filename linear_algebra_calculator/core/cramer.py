from core.matrix import Matrix
from typing import Any, Dict, List, Optional
from utils.printMethods import log_step
from utils.EquationFunctions import format_number, num_to_sub
import copy
from math import isclose

class CramerMethod(Matrix):
    """
    Resuelve sistemas de ecuaciones lineales usando determinantes.
    Funciona para cualquier cantidad de variables definida por el usuario.
    """
    
    def __init__(self, matriz: List[List[float]], b: List[float]) -> None:
        if len(b) != len(matriz):
            raise ValueError("Las variables independientes deben tener la misma cantidad que el numero de ecuaciones")
        
        n = len(matriz)
        # comprobar que cada fila tenga longitud n (matriz n x n)
        if any(len(row) != n for row in matriz):
            raise ValueError("CramerMethod sólo acepta matrices cuadradas (n x n). La matriz recibida no es cuadrada.")
        
        self.matrix_A = copy.deepcopy(matriz)
        self.vector_b = copy.deepcopy(b)
        self.n_variables: int = len(matriz)
        
        self.tolerance: float=1e-12
        
        self.frame: List[Dict[str, Any]] = []
        
        self.determinant_A: Optional[float] = None
        self.solution: Optional[List[float]] = None
    
    #-----------------------
    # DETERMINANTE - REGLA DE SARRUS (solo 3x3)
    #-----------------------
    def calculate_determinant_sarrus(self, matrix: List[List[float]]) -> float:
        """
        Calcula el determinante usando la Regla de Sarrus (solo matrices 3x3).
        Muestra paso a paso las diagonales y productos.
        """
        n = len(matrix)
        if n != 3:
            raise ValueError("La Regla de Sarrus solo aplica para matrices 3x3")

        log_step(self.frame, "═══ MÉTODO: REGLA DE SARRUS (3×3) ═══", matrix, det=None, tag="sarrus_start")

        # Extender matriz (agregar primeras 2 columnas al final)
        extended = [row[:] + row[:2] for row in matrix]
        log_step(self.frame, "Paso 1: Extender matriz (agregar primeras 2 columnas)", extended, det=None, tag="sarrus_extended")

        a11, a12, a13 = matrix[0]
        a21, a22, a23 = matrix[1]
        a31, a32, a33 = matrix[2]

        # Diagonales positivas
        d1_pos = a11 * a22 * a33
        d2_pos = a12 * a23 * a31
        d3_pos = a13 * a21 * a32
        positive = d1_pos + d2_pos + d3_pos

        log_step(self.frame, f"Paso 2: Diagonales principales (↘):", matrix, det=None, tag="sarrus_pos")
        log_step(self.frame, f"  Diagonal 1: ({format_number(a11)})×({format_number(a22)})×({format_number(a33)}) = {format_number(d1_pos)}", matrix, det=None, tag="sarrus_d1")
        log_step(self.frame, f"  Diagonal 2: ({format_number(a12)})×({format_number(a23)})×({format_number(a31)}) = {format_number(d2_pos)}", matrix, det=None, tag="sarrus_d2")
        log_step(self.frame, f"  Diagonal 3: ({format_number(a13)})×({format_number(a21)})×({format_number(a32)}) = {format_number(d3_pos)}", matrix, det=None, tag="sarrus_d3")
        log_step(self.frame, f"  Suma positiva: {format_number(d1_pos)} + {format_number(d2_pos)} + {format_number(d3_pos)} = {format_number(positive)}", matrix, det=None, tag="sarrus_sum_pos")

        # Diagonales negativas
        d1_neg = a13 * a22 * a31
        d2_neg = a11 * a23 * a32
        d3_neg = a12 * a21 * a33
        negative = d1_neg + d2_neg + d3_neg

        log_step(self.frame, f"Paso 3: Diagonales secundarias (↙):", matrix, det=None, tag="sarrus_neg")
        log_step(self.frame, f"  Diagonal 1: ({format_number(a13)})×({format_number(a22)})×({format_number(a31)}) = {format_number(d1_neg)}", matrix, det=None, tag="sarrus_d4")
        log_step(self.frame, f"  Diagonal 2: ({format_number(a11)})×({format_number(a23)})×({format_number(a32)}) = {format_number(d2_neg)}", matrix, det=None, tag="sarrus_d5")
        log_step(self.frame, f"  Diagonal 3: ({format_number(a12)})×({format_number(a21)})×({format_number(a33)}) = {format_number(d3_neg)}", matrix, det=None, tag="sarrus_d6")
        log_step(self.frame, f"  Suma negativa: {format_number(d1_neg)} + {format_number(d2_neg)} + {format_number(d3_neg)} = {format_number(negative)}", matrix, det=None, tag="sarrus_sum_neg")

        det = positive - negative
        log_step(self.frame, f"Paso 4: Determinante = ({format_number(positive)}) - ({format_number(negative)}) = {format_number(det)}", matrix, det=format_number(det), tag="sarrus_result")

        return det

    #-----------------------
    # DETERMINANTE - EXPANSIÓN POR COFACTORES
    #-----------------------
    def calculate_determinant_cofactors(self, matrix: List[List[float]], level: int = 0, show_steps: bool = True) -> float:
        """
        Calcula el determinante usando Expansión por Cofactores.
        Muestra paso a paso los cofactores y signos.
        """
        n = len(matrix)

        if level == 0 and show_steps:
            log_step(self.frame, "═══ MÉTODO: EXPANSIÓN POR COFACTORES ═══", matrix, det=None, tag="cofactor_start")
            log_step(self.frame, f"Matriz {n}×{n} - Expandiendo por la primera fila", matrix, det=None, tag="cofactor_expand")

        # Caso base: matriz 1x1
        if n == 1:
            return matrix[0][0]

        # Caso base: matriz 2x2
        if n == 2:
            det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
            if show_steps and level > 0:
                log_step(self.frame, f"  {'  '*level}Submatriz 2×2: det = ({format_number(matrix[0][0])})×({format_number(matrix[1][1])}) - ({format_number(matrix[0][1])})×({format_number(matrix[1][0])}) = {format_number(det)}", matrix, det=format_number(det), tag=f"cofactor_2x2_level{level}")
            return det

        # Caso recursivo: expansión por la primera fila
        det = 0
        cofactor_details = []

        for j in range(n):
            # Signo del cofactor
            sign = (-1) ** j
            sign_str = "+" if sign > 0 else "-"

            # Elemento de la primera fila
            element = matrix[0][j]

            # Crear submatriz eliminando fila 0 y columna j
            submatrix = [[matrix[i][k] for k in range(n) if k != j] for i in range(1, n)]

            if show_steps and level == 0:
                log_step(self.frame, f"Cofactor C₁{num_to_sub(j+1)}: signo = {sign_str}, elemento = {format_number(element)}", submatrix, det=None, tag=f"cofactor_c1{j+1}")

            # Calcular determinante de la submatriz recursivamente
            sub_det = self.calculate_determinant_cofactors(submatrix, level + 1, show_steps=False)

            # Calcular cofactor
            cofactor = sign * element * sub_det
            det += cofactor

            if show_steps and level == 0:
                log_step(self.frame, f"  C₁{num_to_sub(j+1)} = ({sign_str}1) × ({format_number(element)}) × det(M₁{num_to_sub(j+1)}) = ({sign_str}1) × ({format_number(element)}) × ({format_number(sub_det)}) = {format_number(cofactor)}", submatrix, det=format_number(sub_det), tag=f"cofactor_calc_c1{j+1}")

            cofactor_details.append(f"{sign_str}{format_number(abs(cofactor))}")

        if show_steps and level == 0:
            log_step(self.frame, f"Determinante = {' '.join(cofactor_details)} = {format_number(det)}", matrix, det=format_number(det), tag="cofactor_result")

        return det

    #-----------------------
    # DETERMINANTE (expansion de cofactores)
    #-----------------------
    def calculate_determinant(self, matrix: List[List[float]], show_sarrus: bool = False) -> float :
        n = len(matrix)
        
        # Caso base: matriz 1x1
        if n == 1:
            return matrix[0][0]
        
        # Caso base: matriz 2x2
        if n == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        
        if n==3:
            if show_sarrus:
                extended = [row[:] for row in matrix] + [matrix[0][:], matrix[1][:]]
                log_step(self.frame, "Sarrus - Matriz Extendida", extended, det=None, tag="sarrus")
                
            a11, a12, a13 = matrix[0]
            a21, a22, a23 = matrix[1]
            a31, a32, a33 = matrix[2]
            
            # Regla de Sarrus:
            positive = a11 * a22 * a33 + a12 * a23 * a31 + a13 * a21 * a32
            negative = a13 * a22 * a31 + a11 * a23 * a32 + a12 * a21 * a33
            return positive - negative
        
        # Caso recursivo: expansión por la primera fila
        det = 0
        for j in range(n):
            # Crear submatriz eliminando fila 0 y columna j
            submatrix = [[matrix[i][k] for k in range(n) if k!=j]for i in range(1,n)]
            
            cofactor = ((-1) ** j) * matrix[0][j] * self.calculate_determinant(submatrix)
            det += cofactor
        
        return det
    
    #-----------------------
    # Creacion matriz Cramer
    #-----------------------
    def create_cramer_matrix(self, col_index:int)->List[List[float]]:
        cramer_matrix = []
        for i in range(self.n_variables):
            row = []
            for j in range(self.n_variables):
                row.append(self.vector_b[i] if j==col_index else self.matrix_A[i][j])
            cramer_matrix.append(row)
        return cramer_matrix
    
    #-----------------------
    # Resolver Sistema
    #-----------------------
    def solve(self)->Dict[str,Any]:
        """
        Resuelve el sistema de ecuaciones.
        
        Returns:
            list: Solución del sistema [x₁, x₂, ..., xₙ]
            
        Raises:
            ValueError: Si el sistema no tiene solución única
        """
        self.frame = []
        self.solution = None
        
        # Calculo de determinante
        detA = self.calculate_determinant(self.matrix_A, show_sarrus=(self.n_variables == 3))
        self.determinant_A = detA

        
        log_step(self.frame, "Determinante matriz A",self.matrix_A, det=format_number(detA), tag="Determinante A")
        
        # Si detA != 0 -> solucion unica
        if not isclose(detA, 0.0, abs_tol=self.tolerance):
            solution: List[float] = []
            for col in range(self.n_variables):
                C = self.create_cramer_matrix(col)
                detC = self.calculate_determinant(C, show_sarrus=(self.n_variables == 3))
                xi = detC / detA
                log_step(self.frame, f"Matriz Cramer para x{num_to_sub(col+1)}", C, det = format_number(detC), tag=f"cramer_x{col+1}")
                solution.append(xi)
            self.solution = solution
            
            solution_formatted = [format_number(v) for v in solution]
            log_step(self.frame, f"Solucion por regla de Cramer (particular): [{', '.join(solution_formatted)}]",
                    self.matrix_A, det=format_number(detA), tag="solution")
            
            basic_vars = list(range(self.n_variables))
            free_vars: List[int] = []
            log_step(self.frame, f"Variables basicas: {', '.join('x'+num_to_sub(i+1) for i in basic_vars)} | Variables libres: None",
                    self.matrix_A, det=format_number(detA), tag="vars")
            result = {
            'status': 'unique',
            'solution': solution,
            'basic_vars': basic_vars,
            'free_vars': free_vars,
            'determinant': detA
            }
            return result
        
        
        # Si detA == 0 -> inconsistente
        detC_values = []
        for col in range(self.n_variables):
            C = self.create_cramer_matrix(col)
            detC = self.calculate_determinant(C, show_sarrus=(self.n_variables == 3))
            detC_values.append(detC)
            log_step(self.frame, f"Matriz de Cramer para x{num_to_sub(col+1)}", C,det=format_number(detC), tag=f"cramer_check_x{col+1}")
            
        if any(not isclose(v, 0.0, abs_tol=self.tolerance) for v in detC_values):
            log_step(self.frame, "Determinantes de Cramer no todos cero -> sistema inconsistente", self.matrix_A, det=format_number(detA), tag="inconsistent")
            result = {
            'status': 'inconsistent',
            'solution': None,
            'basic_vars': list(range(self.n_variables)),
            'free_vars': [],
            'determinant': detA
            }
            return result
        
        # Si no se cumplieron las demas, indica que detA == 0 y todos detC == 0 -> infinitas soluciones
        log_step(self.frame, "Determinante de Cramer todos cero -> infinitas soluciones", self.matrix_A, det=format_number(detA), tag="infinite")
        
        
        result = {
            'status': 'infinite',
            'solution': 'Crammer',
            'basic_vars': list(range(self.n_variables)),
            'free_vars': [],
            'determinant': detA
        }
        return result

    
    def verify_solution(self, log: bool = True)->Dict[str, Any]:
        """
        Verifica que la solución encontrada satisfaga todas las ecuaciones.
        
        Returns:
            bool: True si la solución es correcta
        """
        if not self.solution:
            return {'ok':False, 'differences':[]}
        
        diffs: List[float] =[]
        rows_info: List[str] = []
        for i in range(self.n_variables):
            lhs = 0.0
            terms: List[str] =[]
            
            for j in range(self.n_variables):
                coef = self.matrix_A[i][j]
                val = self.solution[j]
                lhs += coef * val
                terms.append(f"{format_number(coef)}*x{num_to_sub(j+1)}")
            rhs = self.vector_b[i]
            diff = abs(lhs-rhs)
            diffs.append(diff)
            rows_info.append((i, lhs, rhs, diff))
            
            if log:
                step = f"Verificacion ecuacion {i+1}: {' + '.join(terms)} = {format_number(rhs)}"
                log_step(self.frame, step, self.matrix_A, det=None, tag="verify")
                log_step(self.frame, f"Resultado: {format_number(lhs)} | Error: {format_number(diff)}", self.matrix_A, det=None, tag="verify")
        ok = all(d <= self.tolerance for d in diffs)
        return {'ok': ok, 'differences': diffs}
    
# Hacer disponible para importación
__all__ = ['CramerMethod']