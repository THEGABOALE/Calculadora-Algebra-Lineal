from django.shortcuts import render
from .gauss import GaussMethod
from .gauss_jordan import GaussJordanMethod
from .fraction_utils import parse_fraction, format_number
from utils.html_display import equation_to_html, summary_to_html, frame_to_html

def home_page(request):
    return render(request, 'calculator/home.html')

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

            matrix = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    cell_value = request.POST.get(f'matrix_{i}_{j}', '').strip()
                    if not cell_value:
                        return render(request, 'calculator/matrix_input.html', {
                            'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                            'error': 'Todos los campos de la matriz deben estar llenos.'
                        })
                    row.append(parse_fraction(cell_value))
                matrix.append(row)

            vector = []
            for i in range(rows):
                vector_value = request.POST.get(f'vector_{i}', '').strip()
                if not vector_value:
                    return render(request, 'calculator/matrix_input.html', {
                        'rows': range(rows), 'cols': range(cols), 'num_rows': rows, 'num_cols': cols,
                        'error': 'Todos los campos del vector deben estar llenos.'
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
            return render(request, 'calculator/matrix_input.html', {
                'rows': range(int(request.POST.get('rows', 0))), 
                'cols': range(int(request.POST.get('cols', 0))),
                'num_rows': int(request.POST.get('rows', 0)), 
                'num_cols': int(request.POST.get('cols', 0)),
                'error': f'Error en la entrada: {e}. Asegúrate de que todos los valores son números o fracciones válidas (ej: 1/2).'
            })
        except Exception as e:
            return render(request, 'calculator/index.html', {'error': f'Ocurrió un error inesperado: {e}'})
            
    return render(request, 'calculator/index.html')