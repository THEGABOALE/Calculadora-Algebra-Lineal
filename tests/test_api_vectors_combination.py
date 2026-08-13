"""
Tests de POST /api/v1/vectors/combination con rest_framework.test.APIClient.

vectors/combination reusa matrix_reduce (Fase 3) para Gauss-Jordan y
core/vector_tools.ax_check para verificar Ax=b -- estos tests comparan
contra esas dos llamadas directas, no reimplementan la lógica.
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

from core.vector_tools import ax_check

URL = '/api/v1/vectors/combination'


class TestVectorCombinationParidad(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_b_es_combinacion_lineal_unica(self):
        # b = 2*e1 + 3*e2, con e1, e2 y un tercer vector dependiente.
        A = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        b = [2.0, 3.0, 5.0]
        r = self.client.post(URL, {'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)

        x_part = r.data['result']['coefficients_particular']
        ax, ok = ax_check(A, x_part, b)

        self.assertTrue(r.data['result']['is_linear_combination'])
        self.assertEqual(r.data['check']['ok'], ok)
        for va, vd in zip(r.data['check']['Ax'], ax):
            self.assertAlmostEqual(va, vd, places=9)

    def test_b_no_es_combinacion_lineal(self):
        # Columnas de A generan sólo el plano z=0; b tiene componente z != 0.
        A = [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]
        b = [1.0, 1.0, 1.0]
        r = self.client.post(URL, {'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertFalse(r.data['result']['is_linear_combination'])
        self.assertEqual(r.data['result']['solution_type'], 'inconsistent')
        self.assertIsNone(r.data['result']['coefficients_particular'])

    def test_gauss_jordan_steps_no_esta_vacio(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        b = [2.0, 3.0]
        r = self.client.post(URL, {'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertGreater(len(r.data['gauss_jordan']['steps']), 0)
        self.assertIn('status', r.data['gauss_jordan']['summary'])


class TestVectorCombinationValidacion(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_dimensiones_inconsistentes_400(self):
        r = self.client.post(URL, {'A': [[1.0, 2.0], [3.0, 4.0]], 'b': [1.0]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_a_vacia_400(self):
        r = self.client.post(URL, {'A': [], 'b': []}, format='json')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
