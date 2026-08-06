from django.shortcuts import render
from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.vector import Vector
from core.vector_tools import linear_combination_verification_steps, matrix_vector_product_steps
from core.matrix_tools import determinant, inverse, rank_of, nullspace_vector, transpose
from utils.EquationFunctions import parse_fraction, format_number
from utils.printMethods import log_step
from utils.html_display import equation_to_html, summary_to_html, frame_to_html, matrix_to_html

def home_page(request):
    return render(request, 'calculator/home.html')

def calculatorMain(request):
    return render(request, 'calculator/calculator_main.html')

def ecuationInput(request):
    if request.method == 'POST':
        rows = int(request.POST['rows'])
        cols = int(request.POST['cols'])
        return render(request, 'calculator/ecuation_input.html', {'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols})
    return render(request, 'calculator/make_matrix.html')

def ecuationResolution(request):
    if request.method == 'POST':
        try:
            rows = int(request.POST['rows'])
            cols = int(request.POST['cols'])
            method = request.POST['method']

            # Siempre inicializar las listas con los valores actuales del POST
            matrix_values_list = []
            for i in range(rows):
                row_vals = []
                for j in range(cols):
                    row_vals.append(request.POST.get(f'matrix_{i}_{j}', ''))
                matrix_values_list.append(row_vals)
            vector_values_list = [request.POST.get(f'vector_{i}', '') for i in range(rows)]

            matrix = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    cell_value = matrix_values_list[i][j].strip()
                    if not cell_value:
                        return render(request, 'calculator/ecuation_input.html', {
                            'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                            'error': 'Todos los campos de la matriz deben estar llenos.',
                            'matrix_values_list': matrix_values_list, 'vector_values_list': vector_values_list
                        })
                    row.append(parse_fraction(cell_value))
                matrix.append(row)

            vector = []
            for i in range(rows):
                vector_value = vector_values_list[i].strip()
                if not vector_value:
                    return render(request, 'calculator/ecuation_input.html', {
                        'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                        'error': 'Todos los campos del vector deben estar llenos.',
                        'matrix_values_list': matrix_values_list, 'vector_values_list': vector_values_list
                    })
                vector.append(parse_fraction(vector_value))

            result = None
            frame = None
            if method == 'gauss':
                solver = GaussMethod(matrix, vector)
                frame = solver.gauss_method()
                result = solver.solve_and_log()
            elif method == 'gauss_jordan':
                solver = GaussJordanMethod(matrix, vector)
                frame = solver.run()
                result = solver.solve_and_log()
            elif method == 'combinacion_lineal':
                # Las columnas de la matriz A son los vectores v1..vk; b es el
                # vector objetivo. Resolver A·x = b con Gauss-Jordan responde
                # exactamente si b es combinación lineal de esos vectores -- es
                # la misma llamada que 'gauss_jordan', con la verificación
                # componente a componente y la conclusión que añade
                # cli/vector_runners.run_vector_combination.
                solver = GaussJordanMethod(matrix, vector)
                frame = solver.run()
                result = solver.solve_and_log()
                sol = result.get('solution')
                if sol is not None:
                    vecs = [Vector([matrix[i][j] for i in range(len(matrix))]) for j in range(len(matrix[0]))]
                    _, steps = linear_combination_verification_steps(sol, vecs, vector)
                    for i, line in enumerate(steps, start=1):
                        log_step(frame, f'Verificación {i}: {line}', None, det=None, tag='lc_verify')
                conclusion = {
                    'unique': 'Conclusión: b ES combinación lineal de los vectores dados, de forma ÚNICA.',
                    'infinite': 'Conclusión: b ES combinación lineal de los vectores dados, en INFINITAS formas.',
                    'inconsistent': 'Conclusión: b NO es combinación lineal de los vectores dados.',
                }.get(result.get('status'))
                if conclusion:
                    log_step(frame, conclusion, None, det=None, tag='lc_conclusion')
            elif method == 'ax':
                # No resuelve un sistema: multiplica A por el vector que el
                # usuario ingresó (reutilizando el campo "vector" del
                # formulario como x, no como b). Sólo tiene sentido cuando
                # cols(A) == filas(A) == len(x), porque el formulario no pide
                # una longitud de x distinta de la de b/rows.
                x_vec = Vector(vector)
                y, steps = matrix_vector_product_steps(matrix, x_vec)
                frame = {}
                log_step(frame, 'Entrada: A y x', matrix, det=None, tag='ax_input')
                for i, line in enumerate(steps, start=1):
                    log_step(frame, f'Fila {i}: {line}', None, det=None, tag='ax_step')
                log_step(frame, f"Resultado: A·x = [{', '.join(format_number(v) for v in y)}]", [y], det=None, tag='ax_result')
                result = {'status': 'ax', 'solution': None, 'basic_vars': [], 'free_vars': []}

            if result and 'solution' in result and result['solution'] is not None and result['solution'] != 'Crammer':
                formatted_solution = [format_number(x) for x in result['solution']]
                result['formatted_solution'] = formatted_solution

            # Preparar HTML para ecuación, resumen y pasos.
            # 'ax' no es un sistema (no hay status/solution al estilo
            # unique/infinite/inconsistent), así que summary_to_html lo
            # mostraría como si fuera un error ("solution-inconsistent",
            # "None (sistema inconsistente)"). Se arma su propio resumen.
            if method == 'ax':
                equation_html = (
                    "<div class='equation-pretty'>A =" + matrix_to_html(matrix) +
                    "x =" + matrix_to_html([vector]) + "</div>"
                )
                summary_html = "<div class='solution-box solution-unique'><span>Producto A·x</span></div>"
            else:
                equation_html = equation_to_html(matrix, vector)
                summary_html = summary_to_html(result)
            frame_html = frame_to_html(frame) if frame else ''

            return render(request, 'calculator/result.html', {
                'result': result,
                'equation_html': equation_html,
                'summary_html': summary_html,
                'frame_html': frame_html,
            })
        except ValueError as e:
            rows = int(request.POST.get('rows', 0))
            cols = int(request.POST.get('cols', 0))
            # Siempre reconstruir las listas con los valores actuales
            matrix_values_list = []
            for i in range(rows):
                row_vals = []
                for j in range(cols):
                    row_vals.append(request.POST.get(f'matrix_{i}_{j}', ''))
                matrix_values_list.append(row_vals)
            vector_values_list = [request.POST.get(f'vector_{i}', '') for i in range(rows)]
            return render(request, 'calculator/ecuation_input.html', {
                'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                'error': f'Error en la entrada: {e}. Asegúrate de que todos los valores son números o fracciones válidas (ej: 1/2).',
                'matrix_values_list': matrix_values_list, 'vector_values_list': vector_values_list
            })
        except Exception as e:
            # También intentar reconstruir las listas si hay error inesperado
            rows = int(request.POST.get('rows', 0))
            cols = int(request.POST.get('cols', 0))
            matrix_values_list = []
            for i in range(rows):
                row_vals = []
                for j in range(cols):
                    row_vals.append(request.POST.get(f'matrix_{i}_{j}', ''))
                matrix_values_list.append(row_vals)
            vector_values_list = [request.POST.get(f'vector_{i}', '') for i in range(rows)]
            return render(request, 'calculator/ecuation_input.html', {
                'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                'error': f'Ocurrió un error inesperado: {e}',
                'matrix_values_list': matrix_values_list, 'vector_values_list': vector_values_list
            })
    # Render inicial: inicializar listas vacías
    rows = int(request.GET.get('rows', 0))
    cols = int(request.GET.get('cols', 0))
    if rows and cols:
        matrix_values_list = [['' for _ in range(cols)] for _ in range(rows)]
        vector_values_list = ['' for _ in range(rows)]
        return render(request, 'calculator/ecuation_input.html', {
            'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
            'matrix_values_list': matrix_values_list, 'vector_values_list': vector_values_list
        })
    return render(request, 'calculator/ecuation_input.html', {
        'matrix_values_list': [], 'vector_values_list': []
    })


## Resolución de operación de vectores ##

def vectorInput(request):
    if request.method == 'POST':
        n = int(request.POST['n'])
        return render(request, 'calculator/vector_form.html', {'n': n, 'range_n': range(n)})
    return render(request, 'calculator/vector_dims.html')

def vectorResolution(request):
    if request.method != 'POST':
        return render(request, 'calculator/vector_dims.html')

    n = int(request.POST.get('n', 0))
    method = request.POST.get('method', '')
    v_values = [request.POST.get(f'v_{i}', '') for i in range(n)]
    w_values = [request.POST.get(f'w_{i}', '') for i in range(n)]

    for values in (v_values, w_values):
        if not all(x.strip() for x in values):
            return render(request, 'calculator/vector_form.html', {
                'n': n, 'range_n': range(n),
                'error': 'Todos los campos de ambos vectores deben estar llenos.',
                'v_values': v_values, 'w_values': w_values,
            })

    try:
        v = Vector([parse_fraction(x.strip()) for x in v_values])
        w = Vector([parse_fraction(x.strip()) for x in w_values])

        frame = {}
        log_step(frame, 'Vectores de entrada: v y w', [v.data, w.data], det=None, tag='input')

        if method == 'suma':
            r = v.add(w)
            titulo = 'Suma: v + w'
        elif method == 'resta':
            r = v.sub(w)
            titulo = 'Resta: v - w'
        elif method == 'producto_punto':
            r = v.dot(w)
            titulo = 'Producto punto: v · w'
        else:
            raise ValueError(f'Operación no reconocida: {method}')

        if isinstance(r, Vector):
            resultado_str = str(r)
            log_step(frame, f'Resultado: {r}', [r.data], det=None, tag='result')
        else:
            resultado_str = format_number(r)
            log_step(frame, f'Resultado: {resultado_str}', None, det=None, tag='result')

        equation_html = (
            "<div class='equation-pretty'>v =" + matrix_to_html([v.data]) +
            "w =" + matrix_to_html([w.data]) + "</div>"
        )
        summary_html = (
            f"<div class='solution-box solution-unique'><span>{titulo}</span></div>"
            f"<br><b>Resultado:</b> {resultado_str}"
        )
        frame_html = frame_to_html(frame)

        return render(request, 'calculator/result.html', {
            'result': {'ok': True},
            'equation_html': equation_html,
            'summary_html': summary_html,
            'frame_html': frame_html,
            'back_url': '/vectorInput/',
        })
    except ValueError as e:
        return render(request, 'calculator/vector_form.html', {
            'n': n, 'range_n': range(n),
            'error': f'Error en la entrada: {e}. Asegúrate de que todos los valores son números o fracciones válidas (ej: 1/2).',
            'v_values': v_values, 'w_values': w_values,
        })


## Operaciones con matrices (determinante, inversa, rango, transpuesta) ##

def matrixInput(request):
    if request.method == 'POST':
        rows = int(request.POST['rows'])
        cols = int(request.POST['cols'])
        return render(request, 'calculator/matrix_form.html', {
            'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols
        })
    return render(request, 'calculator/make_matrix.html')

def matrixOperationResolution(request):
    if request.method != 'POST':
        return render(request, 'calculator/make_matrix.html')

    rows = int(request.POST.get('rows', 0))
    cols = int(request.POST.get('cols', 0))
    method = request.POST.get('method', '')
    matrix_values_list = [
        [request.POST.get(f'matrix_{i}_{j}', '') for j in range(cols)]
        for i in range(rows)
    ]

    for row_vals in matrix_values_list:
        if not all(x.strip() for x in row_vals):
            return render(request, 'calculator/matrix_form.html', {
                'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                'error': 'Todos los campos de la matriz deben estar llenos.',
                'matrix_values_list': matrix_values_list,
            })

    try:
        matrix = [[parse_fraction(cell.strip()) for cell in row] for row in matrix_values_list]

        frame = {}
        log_step(frame, 'Matriz de entrada (A)', matrix, det=None, tag='input')

        if method == 'determinante':
            if rows != cols:
                raise ValueError('El determinante sólo está definido para matrices cuadradas.')
            det = determinant(matrix)
            log_step(frame, f'Determinante: det(A) = {format_number(det)}', matrix, det=det, tag='result')
            titulo = 'Determinante'
            resultado_str = format_number(det)

        elif method == 'inversa':
            if rows != cols:
                raise ValueError('La inversa sólo está definida para matrices cuadradas.')
            inverse(matrix, frame=frame)
            titulo = 'Matriz inversa (A⁻¹)'
            resultado_str = None  # ya quedó registrado en el frame por inverse()

        elif method == 'rango':
            r = rank_of(matrix)
            log_step(frame, f'Rango de A: rango(A) = {r}', matrix, det=None, tag='result')
            nullv = nullspace_vector(matrix)
            if nullv is not None:
                log_step(frame, 'Vector no trivial en el núcleo (Ax = 0)', [nullv], det=None, tag='nullspace')
            titulo = 'Rango'
            resultado_str = str(r)

        elif method == 'transpuesta':
            T, _ = transpose(matrix)
            log_step(frame, 'Matriz traspuesta (Aᵀ)', T, det=None, tag='result')
            titulo = 'Traspuesta'
            resultado_str = None

        else:
            raise ValueError(f'Operación no reconocida: {method}')

        equation_html = f"<div class='equation-pretty'>A = {matrix_to_html(matrix)}</div>"
        summary_html = f"<div class='solution-box solution-unique'><span>{titulo}</span></div>"
        if resultado_str is not None:
            summary_html += f"<br><b>Resultado:</b> {resultado_str}"
        frame_html = frame_to_html(frame)

        return render(request, 'calculator/result.html', {
            'result': {'ok': True},
            'equation_html': equation_html,
            'summary_html': summary_html,
            'frame_html': frame_html,
            'back_url': '/matrixInput/',
        })
    except ValueError as e:
        return render(request, 'calculator/matrix_form.html', {
            'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
            'error': f'Error en la entrada: {e}. Asegúrate de que todos los valores son números o fracciones válidas (ej: 1/2).',
            'matrix_values_list': matrix_values_list,
        })