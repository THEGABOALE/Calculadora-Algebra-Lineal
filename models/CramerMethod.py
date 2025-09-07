from models.Matrix import Matrix
from typing import Any, Dict, List, Optional, Tuple
from utils.printMethods import log_step
from utils.EquationFunctions import format_number, num_to_sub
import copy
from math import isclose
from helpers import inputsmatrix
# For running here
from utils.printMethods import print_frame, print_summary, print_equation

class CramerMethod(Matrix):
    """
    Resuelve sistemas de ecuaciones lineales usando determinantes.
    Funciona para cualquier cantidad de variables definida por el usuario.
    """
    
    def __init__(self, matriz: List[List[float]], b: List[float]) -> None:
        if len(b) != len(matriz):
            raise ValueError("Las variables independientes deben tener la misma cantidad que el numero de ecuaciones")
        
        self.matrix_A = copy.deepcopy(matriz)
        self.vector_b = copy.deepcopy(b)
        self.n_variables: int = len(matriz)
        
        self.tolerance: float=1e-12
        
        self.frame: Dict[str, Dict[str, Any]] = {}
        
        self.determinant_A: Optional[float] = None
        self.solution = Optional[List[float]] = None
    
    #-----------------------
    # DETERMINANTE (expansion de cofactores)
    #-----------------------
    def calculate_determinant(self, matrix: List[List[float]]) -> float :
        n = len(matrix)
        
        # Caso base: matriz 1x1
        if n == 1:
            return matrix[0][0]
        
        # Caso base: matriz 2x2
        if n == 2:
            return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        
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
        self.frame = {}
        self.solution = None
        
        # Calculo de determinante
        detA = self.calculate_determinant(self.matrix_A)
        self.determinant_A = detA
        log_step(self.frame, "Determinante matriz A",self.matrix_A, det=detA, tag="Determinante A")
        
        # Si detA == 0 -> sin solucion
        if isclose(detA, 0.0, abs_tol=self.tolerance):
            log_step(self.frame, "Determinante = 0 -> Sin solucion", self.matrix_A, det=detA, tag="Sin solucion")
            
            result = {
                'status': 'inconsistent',
                'solution': None,
                'basic_vars': list(range(self.n_variables)),
                'free_vars': [],
                'determinant': detA
            }
            return result

        # Calcular cada variable
        solution: List[float] = []
        for col in range(self.n_variables):
            C = self.create_cramer_matrix(col)
            detC = self.calculate_determinant(C)
            vari = detC / detA
            
            log_step(self.frame, f"Matriz de Cramer para x{num_to_sub(col+1)}", C, det=detC, tag=f"cramer_x{col+1}")
            
            solution.append(vari)
        self.solution = solution
        
        # Registrar solucion y variables
        solution_formatted = [format_number(v) for v in solution]
        log_step(self.frame, f"Solucion por regla de Cramer (particular): [{', '.join(solution_formatted)}]",
                self.matrix_A, det=detA, tag="solution")

        basic_vars = list(range(self.n_variables))
        free_vars: List[int] = []
        log_step(self.frame, f"Variables básicas: {', '.join('x'+num_to_sub(i+1) for i in basic_vars)} | Variables libres: None",
                self.matrix_A, det=detA, tag="solution")
        
        result = {
            'status': 'unique',
            'solution': solution,
            'basic_vars': basic_vars,
            'free_vars': free_vars,
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
    
def run_crammer():
    rows, cols = inputsmatrix()
    
    matrix, vector = Matrix.make_equation(rows, cols)
    print(print_equation(matrix, vector))
    crammer = CramerMethod(matrix, vector)
    result = crammer.solve()
    
    print_frame(crammer.frame)
    print(print_equation(matrix, vector))
    print_summary(result)
    
    
# Hacer disponible para importación
__all__ = ['CramerMethod', 'run_crammer']