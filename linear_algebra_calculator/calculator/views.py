from django.shortcuts import render
from .gauss import GaussMethod
from .gauss_jordan import GaussJordanMethod
from .fraction_utils import parse_fraction, format_number
from utils.html_display import equation_to_html, summary_to_html, frame_to_html

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

            if result and 'solution' in result and result['solution'] is not None and result['solution'] != 'Crammer':
                formatted_solution = [format_number(x) for x in result['solution']]
                result['formatted_solution'] = formatted_solution

            # Preparar HTML para ecuación, resumen y pasos
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