from typing import List, Optional
from models.Matrix import Matrix
from utils.printMethods import print_equation

"""
DISPLAY DEL SISTEMA LINEAL (A, b)

Propósito:
- Mostrar en consola la matriz de coeficientes A y el vector b como matriz aumentada: [ A | b ].
- Imprimir el sistema Ax = b en forma algebraica legible reutilizando
  utils.printMethods.print_equation (maneja signos, ±1, fracciones y x₁,x₂,…).

Contratos e invariantes:
- len(b) == filas(A). Si no se cumple, se lanza ValueError.
- No se usan numpy/scipy.
- Formato numérico consistente con Matrix.__str__: redondeo a 4 decimales y
  ancho de columna uniforme para alinear columnas.
- nombres_vars se conserva por compatibilidad, pero aquí se ignora porque
  print_equation ya imprime x₁,x₂,… (si se requiere soporte de nombres
  personalizados, debe extenderse print_equation).

Complejidad:
- Tiempo O(m·n) y memoria adicional O(1), donde m=filas(A), n=columnas(A).
"""

def _fmt(v: float) -> str:
    """Redondeo simple (4 decimales) alineado con Matrix.__str__."""
    return f"{round(v, 4)}"

def _max_cell_width(matrix: Matrix, vector: List[float]) -> int:
    """Ancho por celda para alinear columnas en [ A | b ]."""
    # Longitudes de A
    str_matrix = [[_fmt(x) for x in row] for row in matrix.matriz]
    widths = [len(s) for row in str_matrix for s in row]
    # Longitudes de b
    widths += [len(_fmt(v)) for v in vector]
    # +2 de margen para evitar que las columnas queden pegadas
    return (max(widths) if widths else 0) + 2
    
def mostrar_sistema_ecuaciones(
     matrix: Matrix,
     vector: List[float],
     nombres_vars: Optional[List[str]] = None, # mantenido por compatibilidad (no usado aquí)
     mostrar_matriz: bool = True
    ):
    """
    Imprime [ A | b ] (opcional) y el sistema Ax = b usando print_equation.
    """
    
    if len(vector) != matrix.filas:
        raise ValueError("El vector b debe tener la misma cantidad de filas que la matriz A.")
    
    # [ A | b ] con alineado por columnas
    if mostrar_matriz:
        w = _max_cell_width(matrix, vector)
        print("\nMatriz de coeficientes (A) y vector de términos independientes (b):")
        for i, row in enumerate(matrix.matriz):
            left = " ".join(f"{_fmt(v):<{w}}" for v in row)
            right = f"{_fmt(vector[i]):<{w}}"
            print(f"{left}| {right}")
            
    # Sistema en forma algebraica (delegado a la función oficial)
    print("\nSistema de ecuaciones:")
    print(print_equation(matrix.matriz, vector))

def mostrar_sistema_desde_input(
    cntFilas: int,
    cntColums: int,
    nombres_vars: Optional[List[str]] = None, # mantenido por compatibilidad (no usado aquí)
    mostrar_matriz: bool = True,
) -> None:
    """Conveniencia: pide A y b (make_equation) y muestra el sistema."""
    matriz, vector = Matrix.make_equation(cntFilas, cntColums)
    A = Matrix(matriz)
    mostrar_sistema_ecuaciones(A, vector, nombres_vars, mostrar_matriz)
    