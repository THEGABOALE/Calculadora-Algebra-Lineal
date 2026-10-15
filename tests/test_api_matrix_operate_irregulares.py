"""
Regresión del issue #14: POST /api/v1/matrix/operate con matrices irregulares
(filas de distinta longitud).

MatrixOperateSerializer sólo miraba len(A[0]): con A = [[1, 2], [3]] las
operaciones llegaban a core/ y reventaban con 500 (add, scalar, matmul,
inverse, sum_many) o, peor, transpose respondía 200 con [[1, 2]] y perdía el
3 en silencio. Ahora tienen que responder 400 VALIDATION_ERROR, con el mismo
mensaje que ya usan matrix/reduce, matrix/determinant y matrix/properties.

TestMatrixOperateRectangularesValidas fija la otra mitad: las matrices
rectangulares válidas (no cuadradas incluidas) siguen dando exactamente lo
mismo que core/matrix_tools.
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
    sum_many, sub_many, matmul_chain,
)

URL = '/api/v1/matrix/operate'
IRREGULAR = [[1, 2], [3]]


class TestMatrixOperateIrregulares(unittest.TestCase):
    """Cada caso del issue #14, y la irregularidad en el segundo operando:
    400 VALIDATION_ERROR que nombra el operando irregular, nunca 500 ni 200."""

    def setUp(self):
        # Sin raise_request_exception: un 500 tiene que verse como 500 en el
        # assert, no como una excepción que esconda el status.
        self.client = APIClient(raise_request_exception=False)

    def assertIrregular(self, payload, operando):
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, 400, getattr(r, 'data', None))
        error = r.data['error']
        self.assertEqual(error['code'], 'VALIDATION_ERROR')
        self.assertEqual(
            error['message'],
            {'non_field_errors': [f"Todas las filas de '{operando}' deben tener la misma longitud."]},
        )

    # --- los seis casos documentados en el issue -------------------------

    def test_add_A_irregular(self):
        self.assertIrregular({'operation': 'add', 'A': IRREGULAR, 'B': [[1, 1], [1, 1]]}, 'A')

    def test_scalar_A_irregular(self):
        self.assertIrregular({'operation': 'scalar', 'A': IRREGULAR, 'scalar': 2}, 'A')

    def test_matmul_A_irregular(self):
        self.assertIrregular({'operation': 'matmul', 'A': IRREGULAR, 'B': [[1], [1]]}, 'A')

    def test_inverse_A_irregular(self):
        self.assertIrregular({'operation': 'inverse', 'A': IRREGULAR}, 'A')

    def test_sum_many_irregular(self):
        self.assertIrregular(
            {'operation': 'sum_many', 'matrices': [IRREGULAR, [[1, 1], [1]]]}, 'matrices[0]'
        )

    def test_transpose_irregular_no_pierde_elementos(self):
        # Antes: 200 con [[1, 2]] -- el 3 desaparecía sin aviso.
        self.assertIrregular({'operation': 'transpose', 'A': [[1], [2, 3]]}, 'A')

    def test_inverse_primera_fila_corta(self):
        # len(A[0]) != len(A): antes ya era 400, pero por "debe ser cuadrada",
        # que no describe el problema. La forma se valida antes que la
        # cuadratura.
        self.assertIrregular({'operation': 'inverse', 'A': [[1], [2, 3]]}, 'A')

    # --- irregularidad en el segundo operando ----------------------------

    def test_add_B_irregular(self):
        self.assertIrregular({'operation': 'add', 'A': [[1, 1], [1, 1]], 'B': IRREGULAR}, 'B')

    def test_sub_B_irregular(self):
        self.assertIrregular({'operation': 'sub', 'A': [[1, 1], [1, 1]], 'B': IRREGULAR}, 'B')

    def test_matmul_B_irregular(self):
        self.assertIrregular({'operation': 'matmul', 'A': [[1, 2], [3, 4]], 'B': IRREGULAR}, 'B')

    def test_sum_many_segunda_matriz_irregular(self):
        self.assertIrregular(
            {'operation': 'sum_many', 'matrices': [[[1, 1], [1, 1]], IRREGULAR]}, 'matrices[1]'
        )

    def test_sub_many_tercera_matriz_irregular(self):
        sana = [[1, 1], [1, 1]]
        self.assertIrregular(
            {'operation': 'sub_many', 'matrices': [sana, sana, IRREGULAR]}, 'matrices[2]'
        )

    def test_matmul_chain_matriz_irregular(self):
        self.assertIrregular(
            {'operation': 'matmul_chain', 'matrices': [[[1, 2]], [[1], [2, 3]]]}, 'matrices[1]'
        )


class TestMatrixOperateRectangularesValidas(unittest.TestCase):
    """Matrices válidas de distintas dimensiones, no cuadradas incluidas:
    mismo resultado que core/matrix_tools, como antes del cambio."""

    def setUp(self):
        self.client = APIClient()

    def _matriz(self, payload):
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        return r.data['result']['matrix']

    def test_add_y_sub_2x3(self):
        A = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        B = [[0.5, 0.0, -1.0], [2.0, 2.0, 2.0]]
        self.assertEqual(self._matriz({'operation': 'add', 'A': A, 'B': B}), add_matrices(A, B)[0])
        self.assertEqual(self._matriz({'operation': 'sub', 'A': A, 'B': B}), sub_matrices(A, B)[0])

    def test_scalar_3x1(self):
        A = [[1.0], [2.0], [3.0]]
        self.assertEqual(self._matriz({'operation': 'scalar', 'A': A, 'scalar': 2.5}), scalar_mult(2.5, A)[0])

    def test_transpose_2x3_conserva_todos_los_elementos(self):
        A = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        resultado = self._matriz({'operation': 'transpose', 'A': A})
        self.assertEqual(resultado, transpose(A)[0])
        self.assertEqual(resultado, [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]])

    def test_transpose_fila_unica(self):
        self.assertEqual(self._matriz({'operation': 'transpose', 'A': [[1.0, 2.0, 3.0]]}), [[1.0], [2.0], [3.0]])

    def test_matmul_2x3_por_3x1(self):
        A = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        B = [[1.0], [0.0], [-1.0]]
        self.assertEqual(self._matriz({'operation': 'matmul', 'A': A, 'B': B}), matmul(A, B)[0])

    def test_sum_many_y_sub_many_1x3(self):
        Ms = [[[1.0, 2.0, 3.0]], [[1.0, 1.0, 1.0]], [[0.0, 2.0, 4.0]]]
        self.assertEqual(self._matriz({'operation': 'sum_many', 'matrices': Ms}), sum_many(Ms)[0])
        self.assertEqual(self._matriz({'operation': 'sub_many', 'matrices': Ms}), sub_many(Ms[0], Ms[1:])[0])

    def test_matmul_chain_2x3_3x2_2x1(self):
        Ms = [
            [[1.0, 0.0, 2.0], [0.0, 1.0, 1.0]],
            [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]],
            [[1.0], [-1.0]],
        ]
        self.assertEqual(self._matriz({'operation': 'matmul_chain', 'matrices': Ms}), matmul_chain(Ms)[0])

    def test_operando_irrelevante_no_se_valida(self):
        # 'transpose' sólo usa A: un B irregular que venga de más no cambia
        # la respuesta (comportamiento previo, que se conserva).
        A = [[1.0, 2.0], [3.0, 4.0]]
        self.assertEqual(self._matriz({'operation': 'transpose', 'A': A, 'B': IRREGULAR}), transpose(A)[0])


if __name__ == '__main__':
    unittest.main()
