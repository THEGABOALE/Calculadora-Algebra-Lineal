"""
MATRIZ (estructura de datos)

Contenedor de la matriz de coeficientes. No pide datos por consola: los
constructores interactivos (make_matrix / make_equation) viven en
cli.inputsmatrix, para que el motor quede libre de I/O.
"""

class Matrix():
    def __init__(self, matriz: list[list]) -> None:
        self.matriz = matriz
        self.filas = len(matriz)
        self.columnas = len(matriz[0])

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