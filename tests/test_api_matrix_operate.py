"""
Tests de POST /api/v1/matrix/operate con rest_framework.test.APIClient.

Mismo criterio que tests/test_web_vectores_matrices.py: sin django.test.
TestCase, porque estas vistas no tocan base de datos y no hace falta la
maquinaria de transacciones de prueba de Django (que exige correr con
manage.py test en vez de python -m unittest discover tests).

La mitad de estos tests son de PARIDAD: para cada operación, la respuesta del
endpoint se compara contra la llamada directa a core/matrix_tools -- mismo
método de diff real que se usó para comparar los dos motores de Gauss.
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

from core.matrix_tools import (
    add_matrices, sub_matrices, scalar_mult, transpose, matmul,
    sum_many, sub_many, matmul_chain, inverse,
)

URL = '/api/v1/matrix/operate'


class TestMatrixOperateParidad(unittest.TestCase):
    """Cada operación, comparada byte a byte (valor a valor) contra la
    llamada directa a core/matrix_tools sobre las mismas entradas."""

    def setUp(self):
        self.client = APIClient()

    def _post(self, payload):
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        return r.data

    def test_add(self):
        A, B = [[2.0, 1.0], [1.0, 3.0]], [[1.0, 4.0], [0.0, 2.0]]
        data = self._post({'operation': 'add', 'A': A, 'B': B})
        esperado, _ = add_matrices(A, B)
        self.assertEqual(data['result']['matrix'], esperado)

    def test_sub(self):
        A, B = [[2.0, 1.0], [1.0, 3.0]], [[1.0, 4.0], [0.0, 2.0]]
        data = self._post({'operation': 'sub', 'A': A, 'B': B})
        esperado, _ = sub_matrices(A, B)
        self.assertEqual(data['result']['matrix'], esperado)

    def test_scalar(self):
        A = [[2.0, 1.0, 5.0], [1.0, 3.0, -2.0]]
        data = self._post({'operation': 'scalar', 'A': A, 'scalar': 2.5})
        esperado, _ = scalar_mult(2.5, A)
        self.assertEqual(data['result']['matrix'], esperado)
        self.assertEqual(data['input']['scalar'], 2.5)

    def test_transpose(self):
        A = [[2.0, 1.0, 5.0], [1.0, 3.0, -2.0]]
        data = self._post({'operation': 'transpose', 'A': A})
        esperado, _ = transpose(A)
        self.assertEqual(data['result']['matrix'], esperado)

    def test_matmul(self):
        A, B = [[2.0, 1.0], [1.0, 3.0]], [[1.0, 4.0], [0.0, 2.0]]
        data = self._post({'operation': 'matmul', 'A': A, 'B': B})
        esperado, _ = matmul(A, B)
        self.assertEqual(data['result']['matrix'], esperado)

    def test_sum_many(self):
        mats = [[[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]], [[1.0, 1.0], [1.0, 1.0]]]
        data = self._post({'operation': 'sum_many', 'matrices': mats})
        esperado, _ = sum_many(mats)
        self.assertEqual(data['result']['matrix'], esperado)

    def test_sub_many(self):
        mats = [[[10.0, 10.0], [10.0, 10.0]], [[1.0, 2.0], [3.0, 4.0]], [[1.0, 1.0], [1.0, 1.0]]]
        data = self._post({'operation': 'sub_many', 'matrices': mats})
        esperado, _ = sub_many(mats[0], mats[1:])
        self.assertEqual(data['result']['matrix'], esperado)

    def test_matmul_chain(self):
        mats = [[[1.0, 0.0], [0.0, 1.0]], [[2.0, 0.0], [0.0, 2.0]], [[1.0, 1.0], [0.0, 1.0]]]
        data = self._post({'operation': 'matmul_chain', 'matrices': mats})
        esperado, _ = matmul_chain(mats)
        self.assertEqual(data['result']['matrix'], esperado)

    def test_inverse(self):
        A = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]]
        data = self._post({'operation': 'inverse', 'A': A})
        esperado, _ = inverse([row[:] for row in A])
        for fila_api, fila_directa in zip(data['result']['matrix'], esperado):
            for va, vd in zip(fila_api, fila_directa):
                self.assertAlmostEqual(va, vd, places=9)


class TestMatrixOperateSteps(unittest.TestCase):
    """La forma de 'steps' es la que ResultPretty.tsx consume: array de
    strings para las 7 operaciones simples, {frame:{step_states}, text_steps}
    para inverse, alineado por índice."""

    def setUp(self):
        self.client = APIClient()

    def test_operacion_simple_da_lista_de_strings(self):
        r = self.client.post(URL, {
            'operation': 'add',
            'A': [[1.0, 2.0], [3.0, 4.0]],
            'B': [[1.0, 1.0], [1.0, 1.0]],
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIsInstance(r.data['steps'], list)
        self.assertTrue(all(isinstance(s, str) for s in r.data['steps']))

    def test_inverse_da_step_states_alineado_con_text_steps(self):
        A = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]]
        r = self.client.post(URL, {'operation': 'inverse', 'A': A}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        steps = r.data['steps']
        self.assertIn('frame', steps)
        self.assertIn('text_steps', steps)
        step_states = steps['frame']['step_states']
        text_steps = steps['text_steps']
        self.assertEqual(len(step_states), len(text_steps))
        # 15 pasos confirmados manualmente contra core/matrix_tools.inverse
        # para esta misma matriz.
        self.assertEqual(len(text_steps), 15)
        # El paso 4 escala F2: mismo texto y misma matriz que la corrida
        # directa contra core/, verificado a mano antes de este commit.
        self.assertEqual(text_steps[4], 'F2 -> F2 / 5/2')
        self.assertEqual(step_states[4]['tag'], 'scale')


class TestMatrixOperateValidacion(unittest.TestCase):
    """Errores de forma (400 desde el serializer) vs. errores matemáticos
    de core/ (400 desde la vista, traduciendo el ValueError)."""

    def setUp(self):
        self.client = APIClient()

    def test_operacion_desconocida_400(self):
        r = self.client.post(URL, {'operation': 'no_existe', 'A': [[1.0]]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_add_dimensiones_incompatibles_400(self):
        r = self.client.post(URL, {
            'operation': 'add',
            'A': [[1.0, 2.0]],
            'B': [[1.0], [2.0]],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_matmul_dimensiones_incompatibles_400(self):
        r = self.client.post(URL, {
            'operation': 'matmul',
            'A': [[1.0, 2.0, 3.0]],
            'B': [[1.0, 2.0]],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_inverse_matriz_no_cuadrada_400(self):
        r = self.client.post(URL, {'operation': 'inverse', 'A': [[1.0, 2.0, 3.0]]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_inverse_matriz_singular_400_desde_core(self):
        # Error MATEMATICO, no de forma: la matriz es cuadrada y bien
        # formada, pero core/matrix_tools.determinant la detecta singular.
        # Este 400 tiene que salir del ValueError de core/, no del serializer.
        r = self.client.post(URL, {'operation': 'inverse', 'A': [[1.0, 2.0], [2.0, 4.0]]}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('singular', r.data['error']['message'].lower())


if __name__ == '__main__':
    unittest.main()
