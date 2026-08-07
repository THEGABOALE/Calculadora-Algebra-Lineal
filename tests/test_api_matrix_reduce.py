"""
Tests de POST /api/v1/matrix/reduce con rest_framework.test.APIClient.

Mismo criterio que tests/test_api_matrix_operate.py: APIClient sin
django.test.TestCase, sin base de datos.

TestMatrixReduceParidadCasosLimite es el corazón de esta fase: no alcanza
con el caso feliz. Reusa los mismos casos límite que ya están fijados en
tests/test_gauss.py y tests/test_gauss_jordan.py -- pivote nulo (exige swap
de filas), sin swap de columnas, homogéneo con solución única trivial,
homogéneo con infinitas soluciones, no homogéneo con infinitas y forma
paramétrica, más filas que columnas (dependiente), cuadrada de rango
completo -- más un caso inconsistente y uno rectangular con más columnas que
filas, que no estaban cubiertos ahí. Cada caso se corre con gauss Y con
gauss-jordan, comparando contra la llamada directa a core/.
"""
import os
import sys
import unittest

_LAC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'linear_algebra_calculator')
sys.path.insert(0, _LAC_DIR)

import django
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linear_algebra_calculator.settings')
if not apps.ready:
    django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

from rest_framework.test import APIClient

from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.system_solver.gauss_solver import analyze_argumented, solve_from_upper

URL = '/api/v1/matrix/reduce'

# (nombre, A, b) -- los primeros siete son los mismos sistemas que ya
# fijan tests/test_gauss.py y tests/test_gauss_jordan.py.
CASOS_LIMITE = [
    ('pivote_nulo_exige_swap_filas', [[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]], [3.0, 4.0, 5.0]),
    ('sin_swap_de_columnas', [[2.0, 1.0], [4.0, 3.0]], [5.0, 11.0]),
    ('homogeneo_unica_trivial', [[2.0, 1.0], [1.0, -1.0]], [0.0, 0.0]),
    ('homogeneo_infinitas', [[1.0, 2.0], [2.0, 4.0]], [0.0, 0.0]),
    ('no_homogeneo_infinitas_parametrica', [[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]], [6.0, 12.0]),
    ('mas_filas_que_columnas_dependiente', [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [1.0, 1.0, 2.0]),
    ('cuadrada_rango_completo', [[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0]),
    ('inconsistente', [[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0]),
    ('rectangular_mas_columnas_que_filas', [[1.0, 2.0, 3.0]], [6.0]),
]


def _resolver_directo(metodo, A, b):
    if metodo == 'gauss':
        solver = GaussMethod([row[:] for row in A], list(b))
        solver.gauss_method()
    else:
        solver = GaussJordanMethod([row[:] for row in A], list(b))
        solver.run()
    solver.solve_and_log()
    info = analyze_argumented(solver.matriz)
    solved = solve_from_upper(solver.matriz, pivots=solver.pivots)
    return solver, info, solved


class TestMatrixReduceParidadCasosLimite(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def _comparar(self, metodo, A, b):
        r = self.client.post(URL, {'method': metodo, 'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        summary = r.data['summary']
        steps = r.data['steps']

        solver, info, solved = _resolver_directo(metodo, A, b)

        self.assertEqual(summary['status'], solved['status'])
        self.assertEqual(summary['rank'], info['rank'])
        self.assertEqual(summary['basic_vars'], solved['basic_vars'])
        self.assertEqual(summary['free_vars'], solved['free_vars'])
        # El criterio de siempre: steps[] tiene tantos elementos como pasos
        # tiene el frame real, no una cantidad fija ni recortada.
        self.assertEqual(len(steps), len(solver.frame))

        if solved['solution'] is None:
            self.assertIsNone(summary['solution'])
        else:
            for va, vd in zip(summary['solution'], solved['solution']):
                self.assertAlmostEqual(va, vd, places=9)

    def test_casos_limite_con_gauss(self):
        for nombre, A, b in CASOS_LIMITE:
            with self.subTest(caso=nombre, metodo='gauss'):
                self._comparar('gauss', A, b)

    def test_casos_limite_con_gauss_jordan(self):
        for nombre, A, b in CASOS_LIMITE:
            with self.subTest(caso=nombre, metodo='gauss-jordan'):
                self._comparar('gauss-jordan', A, b)

    def test_gauss_y_gauss_jordan_dan_el_mismo_summary(self):
        # Los dos métodos resuelven el mismo sistema: el summary uniforme
        # (calculado una sola vez en el adaptador, no heredado de cada
        # solve_and_log) no debería depender de cuál se usó.
        A, b = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0]
        r_gauss = self.client.post(URL, {'method': 'gauss', 'A': A, 'b': b}, format='json')
        r_gj = self.client.post(URL, {'method': 'gauss-jordan', 'A': A, 'b': b}, format='json')
        self.assertEqual(r_gauss.data['summary']['status'], r_gj.data['summary']['status'])
        self.assertEqual(r_gauss.data['summary']['rank'], r_gj.data['summary']['rank'])
        for va, vd in zip(r_gauss.data['summary']['solution'], r_gj.data['summary']['solution']):
            self.assertAlmostEqual(va, vd, places=9)


class TestMatrixReduceRankAb(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_sistema_consistente_rankA_igual_rankAb(self):
        r = self.client.post(URL, {'method': 'gauss', 'A': [[2.0, 1.0], [1.0, -1.0]], 'b': [5.0, 1.0]}, format='json')
        ranks = r.data['summary']['ranks']
        self.assertEqual(ranks['rankA'], ranks['rankAb'])

    def test_sistema_inconsistente_rankAb_mayor_a_rankA(self):
        r = self.client.post(URL, {'method': 'gauss', 'A': [[1.0, 1.0], [1.0, 1.0]], 'b': [1.0, 2.0]}, format='json')
        ranks = r.data['summary']['ranks']
        self.assertEqual(r.data['summary']['status'], 'inconsistent')
        self.assertGreater(ranks['rankAb'], ranks['rankA'])


class TestMatrixReduceEntradaAb(unittest.TestCase):
    """El request puede mandar A+b, o la matriz aumentada Ab directa."""

    def setUp(self):
        self.client = APIClient()

    def test_ab_combinado_da_lo_mismo_que_a_y_b_separados(self):
        A, b = [[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0]
        Ab = [[2.0, 1.0, 5.0], [1.0, -1.0, 1.0]]
        r_separado = self.client.post(URL, {'method': 'gauss', 'A': A, 'b': b}, format='json')
        r_ab = self.client.post(URL, {'method': 'gauss', 'Ab': Ab}, format='json')
        self.assertEqual(r_separado.status_code, 200)
        self.assertEqual(r_ab.status_code, 200)
        for va, vd in zip(r_separado.data['summary']['solution'], r_ab.data['summary']['solution']):
            self.assertAlmostEqual(va, vd, places=9)


class TestMatrixReduceValidacion(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_metodo_desconocido_400(self):
        r = self.client.post(URL, {'method': 'no_existe', 'A': [[1.0]], 'b': [1.0]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_falta_b_400(self):
        r = self.client.post(URL, {'method': 'gauss', 'A': [[1.0, 2.0]]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_ab_y_a_juntos_400(self):
        r = self.client.post(URL, {
            'method': 'gauss', 'A': [[1.0]], 'b': [1.0], 'Ab': [[1.0, 1.0]],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_dimensiones_inconsistentes_entre_a_y_b_400(self):
        r = self.client.post(URL, {'method': 'gauss', 'A': [[1.0, 2.0], [3.0, 4.0]], 'b': [1.0]}, format='json')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
