from models.Matrix import Matrix
from typing import List, Optional

def _fmt(value: float) -> str:
    """Redondeo consistente con Matrix.__str__"""
    return f"{round(value, 4)}"

def _max_cell_width(matrix: Matrix, determinantes: Optional[List[float]]) -> int:
    """
    Calcula el ancho de la celda imitando Matrix.__str__:
    ancho := largo_máximo_de_cualquier_celda + 2
    Considera también cualquier vector determinante para que el | b quede alineado
    """
    str_coefs = [[_fmt(v) for v in row] for row in matrix.matriz]
    widths = [len(s) for row in str_coefs for s in row]
    if determinantes is not None and len(determinantes) == matrix.filas:
        widths += [len(_fmt(v)) for v in determinantes]
    return (max(widths) if widths else 0) + 2

def _format_eq_row(coefs: List[float], rhs: float, var_names: List[str]) -> str:
    """
    Crea una fila tipo: a1*x1 + a2*x2 + a3*x3 = b
    con manejo de 0, 1 y -1; y signos limpios.
    """
    
    tokens = []
    first = True
    for c, name in zip(coefs, var_names):
        if c == 0:
            continue
        sign = '-' if c < 0 else '+'
        abs_c = abs(c)
        # 1 y -1 sin número explícito
        core = f"{name}" if abs_c == 1 else f"{_fmt(abs_c)} * {name}"
        
        if first:
            tokens.append(f"-{core}" if c < 0 else core)
            first = False
        else:
            tokens.append(f"{sign} {core}")
            
        left = "0" if not tokens else " ".join(tokens)
        return f"{left} =  {_fmt(rhs)}"
    
    def mostrar_sistema_ecuaciones(
        matrix: Matrix,
        vector_determinante: Optional[List[float]] = None,
        nombres_vars: Optional[List[str]] = None,
        mostrar_matriz: bool = True
    ):
        """
        1) La matriz A alineada y, si se pasa, el vector determinante b (como A | b)
        2) El sistema en forma algebraica: a11*x1 + ... + an*xn = b1
        
        IMPORTANTE: 
        - Si pasas vector_determinante, NO se asume columna aumentada; se usan TODAS las columnas como coeficientes.
        - Si NO pasas vector_determinante, por compatibilidad se asume forma aumentada (última columna = RHS).
        """
        
        if vector_determinante is not None and len(vector_determinante) != matrix.filas:
            raise ValueError("El vector determinante debe tener la misma cantidad de filas que la matriz.")
        
        # Determinar # de variables y RHS según si pasa vector o no
        if vector_determinante is not None:
            num_vars = matrix.columnas
            rhs_list = vector_determinante
        else: 
            # Modo compatiblidad: matrix aumentada (última columna RHS)
            if matrix.columnas < 2:
                raise ValueError("La matriz no parece tener forma válida para ecuaciones.")
            num_vars = matrix.columnas - 1
            rhs_list = [row[-1] for row in matrix.matriz]
            
        # Nombres de las variables
        if nombres_vars is None:
            var_names = [f"x{j + 1}" for j in range(num_vars)]
        else: 
            if len(nombres_vars) != num_vars:
                raise ValueError("La cantidad de nombres de variables no coincide con las columnas de coeficientes.")
            var_names = nombres_vars
        
        #Ancho de celda (alineación) imitando Matrix.__str__
        w = _max_cell_width(matrix, vector_determinante)

        # 1) Mostrar matriz (A | b) con espaciado tipo Matrix.__str__
        print("\nMatriz de coeficientes (A) y vector determinante (b):")
        for i, row in enumerate(matrix.matriz):
            # Si usamos vector_determinante, TODA la fila son coeficientes
            # si no, la última columna es RHS, así que solo mostramos coeficientes a la izquierda
            coefs_to_show = row[: num_vars]
            left = " ".join(f"{_fmt(v):<{w}}" for v in coefs_to_show)
            if rhs_list is not None:
                right = f"{_fmt(rhs_list[i]):<{w}}"
                print(f"{left}| {right}")
            else:
                print(left)
        
        # 2) Mostrar sistema en forma algebraica
        print("\nSistema de ecuaciones: ")
        for i in range(matrix.filas):
            coefs = matrix.matriz[i][:num_vars]
            rhs = rhs_list[i]
            ecuacion = _format_eq_row(coefs, rhs, var_names)
            print(ecuacion)
