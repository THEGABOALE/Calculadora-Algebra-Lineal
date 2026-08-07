"""
Helpers para mostrar resultados de álgebra lineal en HTML seguro.
Convierte matrices, ecuaciones, resúmenes y logs a HTML usando fracciones/enteros.
"""
from utils.EquationFunctions import num_to_sub, format_number
from typing import List, Dict, Any, Optional

def equation_to_html(matriz: List[List[float]], vector: List[float]) -> str:
    """Devuelve el sistema Ax = b en HTML, usando fracciones/enteros."""
    filas = len(matriz)
    columnas = len(matriz[0])
    lines = []
    for i in range(filas):
        terms = []
        for j in range(columnas):
            coef = matriz[i][j]
            if abs(coef) < 1e-12:
                continue
            var = f"x<sub>{num_to_sub(j+1)}</sub>"
            coef_str = format_number(abs(coef))
            if coef == 1:
                term = f"{var}"
            elif coef == -1:
                term = f"-{var}"
            else:
                term = f"{coef_str}{var}"
            if terms:
                if coef > 0:
                    term = f"+ {term}"
                else:
                    term = f"- {coef_str}{var}" if abs(coef) != 1 else f"-{var}"
            terms.append(term)
        rhs = format_number(vector[i])
        line = " ".join(terms) + f" = {rhs}"
        lines.append(line)
    # Envolver en un recuadro bonito
    return f'<div class="equation-pretty">' + '<br>'.join(lines) + '</div>'

def summary_to_html(result: Optional[Dict[str, Any]]) -> str:
    if result is None:
        return "<em>No hay resultado para mostrar.</em>"
    status = result.get('status', 'unknown')
    basic = result.get('basic_vars', [])
    free = result.get('free_vars', [])
    def vars_to_str(indices):
        if not indices:
            return "None"
        return ", ".join(f"x<sub>{num_to_sub(i+1)}</sub>" for i in indices)
    sol = result.get('solution')
    # Determinar clase de color
    color_class = 'solution-unique' if status == 'unique' else ('solution-infinite' if status == 'infinite' else 'solution-inconsistent')
    status_map = {'unique': 'Única', 'infinite': 'Infinitas', 'inconsistent': 'Inconsistente'}
    status_str = status_map.get(status, status.capitalize())
    html = [f"<div class='solution-box {color_class}'><span>{status_str} solución</span></div>"]
    html.append(f"<b>Variables básicas:</b> {vars_to_str(basic)}")
    html.append(f"<b>Variables libres:</b> {vars_to_str(free)}")
    if sol == 'Crammer':
        html.append("<b>Solución particular:</b> No determinado por Crammer")
    elif sol is not None and sol != 'Crammer':
        sol_formatted = [format_number(v) for v in sol]
        html.append(f"<b>Solución particular:</b> [{', '.join(sol_formatted)}]")
        html.append("<ul>")
        for idx, val in enumerate(sol):
            var_name = f"x<sub>{num_to_sub(idx + 1)}</sub>"
            html.append(f"<li>{var_name} = {format_number(val)}</li>")
        html.append("</ul>")
        if status == 'infinite':
            html.append("<i>Nota: la solución mostrada es una solución particular (variables libres = 0).</i>")
    else:
        html.append("<b>Solución particular:</b> None (sistema inconsistente)")
    return '<br>'.join(html)

def frame_to_html(frame: List[Dict[str, Any]], show_det: bool = True) -> str:
    if not frame or not isinstance(frame, list) or len(frame) == 0:
        return '<em>No hay pasos registrados para este método.</em>'
    html = []
    for payload in frame:
        step = payload.get("text")
        matrix_state = payload.get("matrix")
        det_val = payload.get("det")
        tag = payload.get("tag")
        html.append(f'<div class="step-log">')
        html.append(f'<div class="step-title">{step}</div>')
        if matrix_state:
            html.append('<div class="step-matrix">' + matrix_to_html(matrix_state) + '</div>')
        if show_det and det_val is not None:
            html.append(f"<div class='step-det'>Determinante: {format_number(det_val)}</div>")
        if tag:
            html.append(f"<span class='log-tag'>(tag: {tag})</span>")
        html.append('</div>')
    return '\n'.join(html)

def matrix_to_html(matrix: List[List[float]]) -> str:
    # Formatea la matriz como tabla HTML usando fracciones/enteros y clase bonita
    rows = []
    for row in matrix:
        cells = [f"<td>{format_number(v)}</td>" for v in row]
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<table class='pretty-matrix'>{''.join(rows)}</table>"
