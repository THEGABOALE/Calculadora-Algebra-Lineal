from typing import List, Optional
from models.Matrix import Matrix
from utils.printMethods import print_equation

def _fmt(value: float) -> str:
    """Redondeo consistente con Matrix.__str__"""
    return f"{round(value, 4)}"

def _fmt(v: float) -> str:
    return f"{round(v, 4)}"

def _max_cell_width(matrix: Matrix, vector: List[float]) -> int:
    # Mismo criterio de Matrix.__str__: ancho máx de celdas + 2
    str_matrix = [[_fmt(x) for x in row] for row in matrix.matriz]
    widths = [len(s) for row in str_matrix for s in row]
    widths += [len(_fmt(v)) for v in vector]
    return (max(widths) if widths else 0) + 2
    
def mostrar_sistema_ecuaciones(
     matrix: Matrix,
     vector: List[float],
     nombres_vars: Optional[List[str]] = None,
     mostrar_matriz: bool = True
    ):
    """
    Usa A y b separados (provenientes de Matrix.make_equation).
    No asume matriz aumentada
    """
    
    if len(vector) != matrix.filas:
        raise ValueError("El vector b debe tener la misma cantidad de filas que la matriz A.")
    
    # 1) Alineado tipo A | b
    if mostrar_matriz:
        w = _max_cell_width(matrix, vector)
        print("\nMatriz de coeficientes (A) y vector de términos independientes (b):")
        for i, row in enumerate(matrix.matriz):
            left = " ".join(f"{_fmt(v):<{w}}" for v in row)
            right = f"{_fmt(vector[i]):<{w}}"
            print(f"{left}| {right}")
            
    #2) Sistema en forma alegbraica
    print("\nSistema de ecuaciones:")
    print(print_equation(matrix.matriz, vector))

# Conveniencia: leer directamente con make_equation y mostrar
def mostrar_sistema_desde_input(
    cntFilas: int,
    cntColums: int,
    nombres_vars: Optional[List[str]] = None,
    mostrar_matriz: bool = True,
) -> None:
    matriz, vector = Matrix.make_equation(cntFilas, cntColums)
    A = Matrix(matriz)
    mostrar_sistema_ecuaciones(A, vector, nombres_vars, mostrar_matriz)
    