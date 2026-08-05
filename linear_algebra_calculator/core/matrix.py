from utils.EquationFunctions import parse_fraction

class Matrix():
    def __init__(self, matriz: list[list]) -> None:
        self.matriz = matriz
        self.filas = len(matriz)
        self.columnas = len(matriz[0])
        
    @staticmethod
    def make_matrix(cntFilas: int, cntColums: int) -> list[list[float]]:
        matriz = []
        valid_values = set("0123456789.-/ ")
        for fila in range(cntFilas):
            while True:
                try:
                    print(f"Ingrese {cntColums} valores para la fila {fila+1}: ")
                    inputs = input(" -> ")
                    ''' Validar las entradas usando valid_values '''
                    if not all(char in valid_values for char in inputs):
                        raise ValueError("La entrada es inválida, ingrese los valores correctamente...")
                    
                    content = list(map(parse_fraction, inputs.split()))
                    
                    ''' Verificar la cantidd de numeros ingresados por fila '''
                    if len(content) != cntColums:
                        raise ValueError(f"Introduce {cntColums} en total, intente nuevamente...")
                    matriz.append(content)
                    break
                except ValueError:
                    print(ValueError)
        return matriz
    
    @staticmethod
    def make_equation(cntFilas: int, cntColums: int):
        matriz = []
        vector = []
        valid_values = set("0123456789.-/ ")
        
        for fila in range(cntFilas):
            while True:
                try:
                    print(f"Ingrese {cntColums} valores para la fila {fila+1}: ")
                    inputs = input(" -> ")
                    if not all(char in valid_values for char in inputs):
                        raise ValueError("La entrada es inválida, intente nuvamente...")
                    content = list(map(parse_fraction, inputs.split()))
                    if len(content) != cntColums:
                        raise ValueError(f"Introduce {cntColums} valores en total...")
                    matriz.append(content)
                    break
                except ValueError:
                    print(ValueError)
            
            while True:
                try:
                    eq = parse_fraction(input(f"Ingrese la equivalencia para la fila {fila+1}: "))
                    vector.append(eq)
                    break
                except ValueError:
                    print(ValueError)
        return matriz, vector
    
    def __str__(self) -> str:
        ''' Redondear los valores y convertirlos a string '''
        str_matrix = [[f"{round(value, 4)}" for value in row] for row in self.matriz]
        
        ''' Calcular el ancho max de columna para alinear '''
        max_width = max(len(item) for row in str_matrix for item in row) + 2
        
        ''' Imprimir la Matrix '''
        lines = []
        for row in str_matrix:
            formatted_rows = " ".join(f"{item:<{max_width}}" for item in row)
            lines.append(formatted_rows)
        return "\n".join(lines)