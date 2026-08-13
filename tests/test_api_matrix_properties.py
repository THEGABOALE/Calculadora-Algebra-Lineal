"""
Tests de POST /api/v1/matrix/properties con rest_framework.test.APIClient.

Mismo criterio que el resto de tests/test_api_*.py: APIClient sin
django.test.TestCase, sin base de datos.

Las matrices reusan las de tests/test_matrix_tools.py en vez de inventar
casos nuevos: la singular ([[1,2],[2,4]], filas dependientes) de
test_singular_matrix/test_nullspace_nontrivial_and_verify, y la regular
([[4,7],[2,6]]) de test_inverse_2x2. La paridad se compara contra
core/matrix_tools llamado directo, no contra un valor fijado a mano.
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

from core.matrix_tools import is_singular, nullspace_vector, rank_of

URL = '/api/v1/matrix/properties'

# Las mismas matrices que ya fija tests/test_matrix_tools.py.
SINGULAR = [[1.0, 2.0], [2.0, 4.0]]  # filas dependientes -- test_singular_matrix, test_nullspace_nontrivial_and_verify
REGULAR = [[4.0, 7.0], [2.0, 6.0]]   # invertible -- test_inverse_2x2


class TestMatrixPropertiesParidadConElMotor(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def _comparar(self, A):
        r = self.client.post(URL, {'A': A}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        result = r.data['result']

        self.assertEqual(result['rank'], rank_of(A))
        self.assertEqual(result['is_singular'], is_singular(A))

        nulo_directo = nullspace_vector(A)
        if nulo_directo is None:
            self.assertIsNone(result['nullspace'])
        else:
            for va, vd in zip(result['nullspace'], nulo_directo):
                self.assertAlmostEqual(va, vd, places=9)

    def test_singular(self):
        self._comparar(SINGULAR)

    def test_regular(self):
        self._comparar(REGULAR)

    def test_rectangular(self):
        self._comparar([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])


class TestMatrixPropertiesSingularVsRegular(unittest.TestCase):
    """El criterio que pide la Fase 8: singular -> is_singular:true y núcleo
    no trivial; regular -> nullspace:null."""

    def setUp(self):
        self.client = APIClient()

    def test_singular_da_nucleo_no_trivial(self):
        r = self.client.post(URL, {'A': SINGULAR}, format='json')
        result = r.data['result']
        self.assertTrue(result['is_singular'])
        self.assertIsNotNone(result['nullspace'])
        self.assertEqual(len(result['nullspace']), 2)

    def test_nucleo_satisface_ax_igual_cero(self):
        # Mismo chequeo que test_nullspace_nontrivial_and_verify, pero contra
        # el vector que devuelve la API, no el que devuelve core/ directo.
        r = self.client.post(URL, {'A': SINGULAR}, format='json')
        x = r.data['result']['nullspace']
        for fila in SINGULAR:
            producto = sum(c * xi for c, xi in zip(fila, x))
            self.assertAlmostEqual(producto, 0.0, places=9)

    def test_regular_da_nucleo_null(self):
        r = self.client.post(URL, {'A': REGULAR}, format='json')
        result = r.data['result']
        self.assertFalse(result['is_singular'])
        self.assertIsNone(result['nullspace'])
        self.assertIsNone(result['nullspace_pretty'])

    def test_regular_rango_completo(self):
        r = self.client.post(URL, {'A': REGULAR}, format='json')
        self.assertEqual(r.data['result']['rank'], 2)

    def test_singular_rango_deficiente(self):
        r = self.client.post(URL, {'A': SINGULAR}, format='json')
        self.assertEqual(r.data['result']['rank'], 1)


class TestMatrixPropertiesNoCuadrada(unittest.TestCase):
    """rank_of y nullspace_vector aceptan rectangulares; is_singular no está
    definida ahí y devuelve None -- no se rechaza en el serializer."""

    def setUp(self):
        self.client = APIClient()

    def test_rectangular_no_es_400(self):
        r = self.client.post(URL, {'A': [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]}, format='json')
        self.assertEqual(r.status_code, 200)

    def test_rectangular_is_singular_null(self):
        r = self.client.post(URL, {'A': [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]}, format='json')
        self.assertIsNone(r.data['result']['is_singular'])


class TestMatrixPropertiesValidacion(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_falta_a_400(self):
        r = self.client.post(URL, {}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_a_vacia_400(self):
        r = self.client.post(URL, {'A': []}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_filas_de_distinta_longitud_400(self):
        r = self.client.post(URL, {'A': [[1.0, 2.0], [3.0]]}, format='json')
        self.assertEqual(r.status_code, 400)


class TestMatrixPropertiesInputViaja(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_input_operation_es_properties(self):
        r = self.client.post(URL, {'A': REGULAR}, format='json')
        self.assertEqual(r.data['input']['operation'], 'properties')
        self.assertEqual(r.data['input']['A'], REGULAR)


if __name__ == '__main__':
    unittest.main()
