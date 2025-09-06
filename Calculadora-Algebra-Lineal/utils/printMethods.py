"""
PAra imprimir y registrar pasos de métodos de álgebra lineal.

Funciones diseñadas para ser independientes de los models. Se espera un frame
con la estructura:
dict[step_str] -> {"matrix": list[list[float]], "det": Optional[float], "tag": Optional[str]}
"""

from __future__ import annotations
import copy 
from typing import Any, Callable, Dict, List, Optional
from utils.EquationFunctions import num_to_sub, format_number, parse_fraction
Frame = Dict[str, Dict[str, Any]]

def log_step(frame: Frame, step: str, matrix_state: List[List[float]], det: Optional[float] = None, tag: Optional[str] = None) -> None:
    """Añade un paso al `frame`.
    - frame: diccionario donde se guardan los pasos.
    - step: descripción legible del paso.
    - matrix_state: estado de la matriz (se hace deepcopy internamente).
    - det: valor del determinante (si aplica) o None.
    - tag: etiqueta corta (ej. 'swap', 'elim', 'det').
    """
    frame[step] = {"matrix": copy.deepcopy(matrix_state), "det": det, "tag":tag}
    
    
def _to_str_cell(value: Any) -> str:
    try:
        return format_number(float(value))
    except Exception:
        return str(value)
    
def format_matrix(matrix: List[List[float]]) -> str:
    if not matrix:
        return ""
    
    str_rows: List[List[str]] = [[_to_str_cell(v) for v in row] for row in matrix]
    cols = len(str_rows[0])
    col_widths = [0] * cols
    for i in str_rows:
        for j in range(cols):
            col_widths[j] = max(col_widths[j], len(i[j]))
            
    lines: List[str] = []
    for r in str_rows:
        padded = [r[i].ljust(col_widths[i]) for i in range(cols)]
        lines.append("  ".join(padded))
    return "\n".join(lines)

def print_frame(frame: Frame, show_det: bool = True, sep: str = "-"*40)->None:
    for step, payload in frame.items():
        matrix_state = payload.get("matrix")
        det_val = payload.get("det")
        tag = payload.get("tag")
        print(step)
        if matrix_state:
            print(format_matrix(matrix_state)) 
        if show_det and det_val is not None:
            try:
                print("Determinante:", parse_fraction(float(det_val)))
            except Exception:
                print("Determinante:", det_val)
        if tag:
            print(f"(tag: {tag})")
        print(sep)
    
__all__ = ["log_step", "format_matrix", "print_frame"]

def print_equation(matriz: list[list], vector: list[float]) -> str:
    filas = len(matriz)
    columnas = len(matriz[0])
    lines = []
    for i in range(filas):
        terms = []
        for j in range(columnas):
            coef = matriz[i][j]
            if abs(coef) < 1e-12:
                continue
            
            var = f"x{num_to_sub(j+1)}"
            coef_str = format_number(abs(coef))
            
            if coef == 1:
                term = f"{var}"
            elif coef == -1:
                term = f"-{var}"
            else:
                term =f"{coef_str}{var}"
                
            if terms:
                if coef > 0:
                    term = f"+ {term}"
                else:
                    term = f"- {coef_str}{var}" if abs(coef) != 1 else f"-{var}"
            terms.append(term)
            
        rhs = format_number(vector[i])
        line = " ".join(terms) + f" = {rhs}"
        lines.append(line)
        
    return "\n".join(lines)

def print_summary(result: Optional[Any]):
    if result is None:
        print("No hay resultado para mostrar.")
        return

    print("============ SUMMARY ============")
    status = result.get('status', 'unknown')
    print(f"Status: {status}")

    basic = result.get('basic_vars', [])
    free = result.get('free_vars', [])

    def vars_to_str(indices):
        if not indices:
            return "None"
        return ", ".join(f"x{num_to_sub(i+1)}" for i in indices)

    print(f"Variables básicas: {vars_to_str(basic)}")
    print(f"Variables libres: {vars_to_str(free)}")

    sol = result.get('solution')
    if sol is not None:
        # vector compacto formateado
        sol_formatted = [format_number(v) for v in sol]
        print(f"Solución particular: [{', '.join(sol_formatted)}]")

        # detalle variable por variable
        print("\nValores por variable:")
        for idx, val in enumerate(sol):
            var_name = f"x{num_to_sub(idx + 1)}"
            print(f"  {var_name} = {format_number(val)}")

        if status == 'infinite':
            print("\nNota: la solución mostrada es una solución particular (variables libres = 0).")
    else:
        print("Solución particular: None (sistema inconsistente)")
    print("=================================")