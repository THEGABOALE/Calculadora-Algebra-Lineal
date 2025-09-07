from models.Matrix import Matrix
from typing import List, Optional

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
    
    num_vars = matrix.columnas
    if nombres_vars is None:
        var_names = [f"x{j+1}" for j in range(num_vars)]
    else:
        if len(nombres_vars) != num_vars:
            raise ValueError("La cantidad de nombres de variables no coincide con las columnas de A.")
        var_names = nombres_vars
        
    w = _max_cell_width(matrix, vector)
    
    # 1) Alineado tipo A | b
    if mostrar_matriz:
        print("\nMatriz de coeficientes (A) y vector de términos independientes (b):")
        for i, row in enumerate(matrix.matriz):
            left = " ".join(f"{_fmt(v):<{w}}" for v in row)
            right = f"{_fmt(vector[i]):<{w}}"
            print(f"{left}| {right}")
            
    #2) Sistema en forma alegbraica
    print("\nSistema de ecuaciones:")
    for i in range(matrix.filas):
        coefs = matrix.matriz[i]
        rhs = vector[i]
        tokens, first = [], True
        for c, name in zip(coefs, var_names):
            if c == 0:
                continue
            sign = '-' if c < 0 else '+'
            abs_c = abs(c)
            core = name if abs_c == 1 else f"{_fmt(abs_c)}*{name}"
            if first:
                tokens.append(f"-{core}" if c < 0 else core)
                first = False
            else:
                tokens.append(f"{sign} {core}")
        left = "0" if not tokens else " ".join(tokens)
        print(f"{left} = {_fmt(rhs)}")

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
    