class CramerMethod:
    """
    Resuelve sistemas de ecuaciones lineales usando determinantes.
    Funciona para cualquier cantidad de variables definida por el usuario.
    """
    
    def __init__(self):
        self.matrix_A = []
        self.vector_b = []
        self.n_variables = 0
        self.solution = []
        self.determinant_A = 0
    
    def calculate_determinant(self, matrix):
        """
        Calcula el determinante de una matriz cuadrada usando expansión por cofactores.
        
        Args:
            matrix: Lista de listas representando la matriz
            
        Returns:
            float: El determinante de la matriz
        """
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
            submatrix = []
            for i in range(1, n):
                row = []
                for k in range(n):
                    if k != j:
                        row.append(matrix[i][k])
                submatrix.append(row)
            
            # Calcular cofactor
            cofactor = ((-1) ** j) * matrix[0][j] * self.calculate_determinant(submatrix)
            det += cofactor
        
        return det
    
    def create_cramer_matrix(self, col_index):
        """
        Crea una matriz reemplazando la columna especificada con el vector de términos independientes.
        
        Args:
            col_index: Índice de la columna a reemplazar (0-indexado)
            
        Returns:
            list: Matriz con la columna reemplazada
        """
        cramer_matrix = []
        for i in range(self.n_variables):
            row = []
            for j in range(self.n_variables):
                if j == col_index:
                    row.append(self.vector_b[i])
                else:
                    row.append(self.matrix_A[i][j])
            cramer_matrix.append(row)
        return cramer_matrix
    
    def input_system(self):
        """
        Permite al usuario ingresar el sistema de ecuaciones.
        """
        print("Ingrese el número de variables (ecuaciones):")
        self.n_variables = int(input())
        
        print(f"\nIngrese los coeficientes para {self.n_variables} ecuaciones:")
        print("Para cada ecuación, ingrese los coeficientes separados por espacios")
        
        # Ingresar matriz de coeficientes
        self.matrix_A = []
        for i in range(self.n_variables):
            print(f"Ecuación {i+1} - Coeficientes de x₁ hasta x₍{self.n_variables}₎:")
            coefficients = list(map(float, input().split()))
            if len(coefficients) != self.n_variables:
                raise ValueError(f"Se esperaban {self.n_variables} coeficientes, se recibieron {len(coefficients)}")
            self.matrix_A.append(coefficients)
        
        # Ingresar vector de términos independientes
        print(f"\nIngrese los {self.n_variables} términos independientes separados por espacios:")
        self.vector_b = list(map(float, input().split()))
        if len(self.vector_b) != self.n_variables:
            raise ValueError(f"Se esperaban {self.n_variables} términos independientes")
    
    def solve(self):
        """
        Resuelve el sistema de ecuaciones.
        
        Returns:
            list: Solución del sistema [x₁, x₂, ..., xₙ]
            
        Raises:
            ValueError: Si el sistema no tiene solución única
        """
        # Calcular determinante de la matriz principal
        self.determinant_A = self.calculate_determinant(self.matrix_A)
        
        if abs(self.determinant_A) < 1e-10:
            raise ValueError("El sistema no tiene solución única (determinante = 0)")
        
        # Calcular cada variable usando la regla de Cramer
        self.solution = []
        for i in range(self.n_variables):
            # Crear matriz reemplazando la columna i con el vector b
            cramer_matrix = self.create_cramer_matrix(i)
            
            # Calcular determinante de la matriz de Cramer
            det_cramer = self.calculate_determinant(cramer_matrix)
            
            # Calcular la variable xi
            xi = det_cramer / self.determinant_A
            self.solution.append(xi)
        
        return self.solution
    
    def display_solution(self):
        """
        Muestra la solución del sistema de manera formatada.
        """
        if not self.solution:
            print("No se ha resuelto ningún sistema.")
            return
        
        print("\n" + "="*50)
        print("SOLUCIÓN DEL SISTEMA")
        print("="*50)
        
        for i, value in enumerate(self.solution, 1):
            print(f"x₍{i}₎ = {value:.6f}")
        
        print(f"\nDeterminante de la matriz principal: {self.determinant_A:.6f}")
    
    def verify_solution(self):
        """
        Verifica que la solución encontrada satisfaga todas las ecuaciones.
        
        Returns:
            bool: True si la solución es correcta
        """
        if not self.solution:
            return False
        
        print("\n" + "="*50)
        print("VERIFICACIÓN DE LA SOLUCIÓN")
        print("="*50)
        
        is_correct = True
        tolerance = 1e-10
        
        for i in range(self.n_variables):
            # Calcular el lado izquierdo de la ecuación
            left_side = 0
            equation_str = ""
            for j in range(self.n_variables):
                term = self.matrix_A[i][j] * self.solution[j]
                left_side += term
                if j > 0:
                    equation_str += " + " if self.matrix_A[i][j] >= 0 else " "
                equation_str += f"{self.matrix_A[i][j]:.3f}*x₍{j+1}₎"
            
            # Comparar con el término independiente
            difference = abs(left_side - self.vector_b[i])
            is_equation_correct = difference < tolerance
            is_correct = is_correct and is_equation_correct
            
            status = "✓" if is_equation_correct else "✗"
            print(f"Ecuación {i+1}: {equation_str} = {self.vector_b[i]:.6f}")
            print(f"            Resultado: {left_side:.6f} {status}")
            print(f"            Error: {difference:.2e}")
            print()
        
        return is_correct
    
    def run(self):
        """
        Ejecuta el proceso completo: entrada, resolución y verificación.
        """
        try:
            self.input_system()
            self.solve()
            self.display_solution()
            
            print("\n¿Desea verificar la solución? (s/n):")
            if input().lower().startswith('s'):
                is_correct = self.verify_solution()
                if is_correct:
                    print("✓ La solución es correcta.")
                else:
                    print("✗ La solución tiene errores.")
        
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")


# Función auxiliar para uso directo
def system_solver():
    """
    Función de conveniencia para resolver un sistema directamente.
    """
    cramer = CramerMethod()
    cramer.run()


# Solo ejecutar si se llama directamente, no al importar
if __name__ == "__main__":
    system_solver()
    
# Hacer disponible para importación
__all__ = ['CramerMethod', 'system_solver']