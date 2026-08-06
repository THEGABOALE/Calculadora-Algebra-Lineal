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
    if sol == 'Crammer':
        print("Solucion particular: No determinado por Crammer")
    elif sol is not None and sol != 'Crammer':
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
    # Mostrar determinante / singularidad si están en el resultado
    det = result.get('determinant') if isinstance(result, dict) else None
    if det is not None:
        try:
            print(f"Determinante de A: {format_number(det)}")
        except Exception:
            print(f"Determinante de A: {det}")

    sing = result.get('is_singular') if isinstance(result, dict) else None
    if sing is not None:
        if sing is True:
            print("Estado: Matriz SINGULAR (no invertible)")
        elif sing is False:
            print("Estado: Matriz NO SINGULAR (invertible)")
        else:
            print(f"Estado de singularidad: {sing}")
    print("=================================")

# ---- NUEVO: presentación de determinantes (Cramer/Sarrus/Cofactores) ----
def print_determinant_menu():
    """
    Muestra el menú de métodos para calcular determinantes.
    """
    print("\n╔═══════════════════════════════════════════════╗")
    print("║   MÉTODOS PARA CALCULAR DETERMINANTES         ║")
    print("╚═══════════════════════════════════════════════╝")
    print("[1] Método de Cramer (básico)")
    print("[2] Regla de Sarrus (solo 3×3)")
    print("[3] Expansión por Cofactores (cualquier n×n)")
    print("[4] Comparar todos los métodos (solo 3×3)")
    print("[0] Volver al menú principal")
    print("═" * 47)

def print_determinant_result(matrix: List[List[float]], det: float, method_name: str):
    """
    Imprime el resultado del cálculo de determinante.
    """
    print("\n" + "═" * 50)
    print(f"RESULTADO - {method_name}")
    print("═" * 50)
    print("Matriz:")
    print(format_matrix(matrix))
    print(f"\nDeterminante: {format_number(det)}")
    print("═" * 50)

def compare_determinant_methods(cramer_obj, matrix: List[List[float]]):
    """
    Compara los tres métodos de cálculo de determinante (solo para 3×3).
    """
    n = len(matrix)
    if n != 3:
        print("\nError: La comparación de métodos solo está disponible para matrices 3×3.")
        return

    print("\n" + "═" * 60)
    print("COMPARACIÓN DE MÉTODOS PARA CALCULAR DETERMINANTE (3×3)")
    print("═" * 60)
    print("\nMatriz original:")
    print(format_matrix(matrix))

    results = {}

    # Método 1: Cramer (básico)
    print("\n" + "─" * 60)
    print("MÉTODO 1: CRAMER (BÁSICO)")
    print("─" * 60)
    cramer_obj.frame = {}
    det1 = cramer_obj.calculate_determinant(matrix, show_sarrus=False)
    results['Cramer'] = det1
    print(f"Determinante (Cramer): {format_number(det1)}")

    # Método 2: Sarrus
    print("\n" + "─" * 60)
    print("MÉTODO 2: REGLA DE SARRUS")
    print("─" * 60)
    cramer_obj.frame = {}
    det2 = cramer_obj.calculate_determinant_sarrus(matrix)
    results['Sarrus'] = det2
    print_frame(cramer_obj.frame, show_det=False)
    print(f"Determinante (Sarrus): {format_number(det2)}")

    # Método 3: Cofactores
    print("\n" + "─" * 60)
    print("MÉTODO 3: EXPANSIÓN POR COFACTORES")
    print("─" * 60)
    cramer_obj.frame = {}
    det3 = cramer_obj.calculate_determinant_cofactors(matrix)
    results['Cofactores'] = det3
    print_frame(cramer_obj.frame, show_det=False)
    print(f"Determinante (Cofactores): {format_number(det3)}")

    # Resumen comparativo
    print("\n" + "═" * 60)
    print("RESUMEN COMPARATIVO")
    print("═" * 60)
    for method, det_val in results.items():
        print(f"{method:15s}: {format_number(det_val)}")

    # Verificar consistencia
    all_equal = all(abs(det_val - det1) < 1e-10 for det_val in results.values())
    if all_equal:
        print("\n✓ Todos los métodos producen el mismo resultado")
    else:
        print("\n⚠ ADVERTENCIA: Los métodos producen resultados diferentes")
    print("═" * 60)

# ---- NUEVO/ACTUALIZADO: forma paramétrica desde RREF ----
def print_parametric_solution_from_rref(U: List[List[float]], tol: float = 1e-12, param_base: str = "s") -> str:
    """
    Recibe una aumentada en RREF (m x (n+1)) y devuelve una representación
    legible de la solución en forma paramétrica:
      - Variables libres = parámetros s1, s2, ...
      - Variables básicas en función de esos parámetros.
    Si el sistema es inconsistente, lo indica.
    """
    if not U:
        return "Sistema vacío: solución única (vector vacío)."

    m = len(U)
    n = len(U[0]) - 1
    rhs_col = n

    # Fila inconsistente: 0..0 | c≠0
    for r in range(m):
        if all(abs(U[r][c]) <= tol for c in range(n)) and abs(U[r][rhs_col]) > tol:
            return "Sistema inconsistente (0 = c≠0)."

    # Detectar pivotes (primer 1 por fila)
    pivot_col = [-1] * m
    has_pivot = [False] * n
    for r in range(m):
        for c in range(n):
            if abs(U[r][c] - 1.0) <= tol and all(abs(U[r][k]) <= tol for k in range(c)):
                pivot_col[r] = c
                has_pivot[c] = True
                break

    basic = [c for c in range(n) if has_pivot[c]]
    free  = [c for c in range(n) if not has_pivot[c]]

    # asignar nombres de parámetros s1, s2, ...
    param_name = {c: f"{param_base}{idx+1}" for idx, c in enumerate(free)}

    # Única solución
    if not free:
        x = [0.0] * n
        for r, c in enumerate(pivot_col):
            if c != -1: x[c] = U[r][rhs_col]
        xs = ", ".join(f"x{num_to_sub(i+1)} = {format_number(x[i])}" for i in range(n))
        return "Única solución:\n" + xs

    # Infinitas: x_basic = rhs - sum(coeff*param)
    lines = []
    for r in range(m):
        c = pivot_col[r]
        if c == -1: continue
        parts = [format_number(U[r][rhs_col])]
        for j in range(c+1, n):
            coeff = U[r][j]
            if abs(coeff) <= tol: continue
            sgn = "-" if coeff > 0 else "+"
            mag = abs(coeff)
            mag_str = "" if abs(mag-1.0) <= tol else format_number(mag)
            parts.append(f"{sgn} {mag_str}{param_name.get(j, f'x{num_to_sub(j+1)}')}".strip())
        lines.append(f"x{num_to_sub(c+1)} = " + (" ".join(parts)))

    # Declaración de parámetros
    params = ", ".join(f"x{num_to_sub(j+1)} = {param_name[j]}" for j in free)
    lines.append(f"(Parámetros: {params})")
    return "\n".join(lines)

__all__ = ["log_step", "format_matrix", "print_frame", "print_equation",
           "print_summary", "print_parametric_solution_from_rref",
           "print_determinant_menu", "print_determinant_result",
           "compare_determinant_methods"]