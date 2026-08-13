"""
Tests de POST /api/v1/matrix/determinant con rest_framework.test.APIClient.

Mismo criterio que los demás tests de la API: sin django.test.TestCase, sin
base de datos.
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

from core.cramer import CramerMethod

URL = '/api/v1/matrix/determinant'


class TestMatrixDeterminantParidad(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def _comparar(self, method, A):
        r = self.client.post(URL, {'method': method, 'A': A}, format='json')
        self.assertEqual(r.status_code, 200, r.data)

        n = len(A)
        cramer = CramerMethod([row[:] for row in A], [1.0] * n)
        if method == 'sarrus':
            det_directo = cramer.calculate_determinant_sarrus(A)
        else:
            det_directo = cramer.calculate_determinant_cofactors(A)

        self.assertAlmostEqual(r.data['result']['determinant'], det_directo, places=9)
        # Mismo criterio de siempre: la cantidad de estados en la respuesta
        # tiene que coincidir con la cantidad de pasos del frame real.
        self.assertEqual(len(r.data['steps']['frame']['states']), len(cramer.frame))

    def test_sarrus_3x3(self):
        self._comparar('sarrus', [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])

    def test_sarrus_3x3_singular(self):
        self._comparar('sarrus', [[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [1.0, 1.0, 1.0]])

    def test_cofactors_3x3(self):
        self._comparar('cofactors', [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]])

    def test_cofactors_4x4(self):
        self._comparar('cofactors', [
            [1.0, 0.0, 0.0, 2.0], [0.0, 1.0, 0.0, 3.0],
            [0.0, 0.0, 1.0, 4.0], [2.0, 3.0, 4.0, 5.0],
        ])

    def test_sarrus_y_cofactors_coinciden_sobre_la_misma_matriz(self):
        # Mismo chequeo que ya hace tests/test_cramer.py, ahora contra la API.
        A = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]
        r_sarrus = self.client.post(URL, {'method': 'sarrus', 'A': A}, format='json')
        r_cofactors = self.client.post(URL, {'method': 'cofactors', 'A': A}, format='json')
        self.assertAlmostEqual(
            r_sarrus.data['result']['determinant'],
            r_cofactors.data['result']['determinant'],
            places=9,
        )


class TestMatrixDeterminantSteps(unittest.TestCase):
    """La forma de 'steps' para sarrus/cofactors NO es la misma que la de
    inverse en matrix/operate: acá cada estado es autocontenido con su
    propio 'operation', porque ResultPretty.tsx lee result.steps.frame.states
    directo para method in {sarrus, cofactors, cramer}."""

    def setUp(self):
        self.client = APIClient()

    def test_cada_estado_trae_su_propia_operation(self):
        A = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]
        r = self.client.post(URL, {'method': 'sarrus', 'A': A}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        states = r.data['steps']['frame']['states']
        self.assertTrue(all('operation' in st for st in states))
        self.assertGreater(len(states), 0)


class TestMatrixDeterminantCramerRechazado(unittest.TestCase):
    """method=cramer no calcula determinantes -- resuelve sistemas. Se
    rechaza acá con 400 explícito, no se redirige en silencio a cofactores
    (que es el alias falso que tenía el repo del que se porta el frontend)."""

    def setUp(self):
        self.client = APIClient()

    def test_cramer_da_400_con_mensaje_explicativo(self):
        r = self.client.post(URL, {'method': 'cramer', 'A': [[1.0, 0.0], [0.0, 1.0]]}, format='json')
        self.assertEqual(r.status_code, 400)
        mensaje = str(r.data).lower()
        self.assertTrue('resuelve sistemas' in mensaje or 'no calcula' in mensaje)

    def test_cramer_no_devuelve_un_determinante_de_cofactores(self):
        # La regresión puntual a evitar: que 'cramer' calle y devuelva 200
        # con el mismo numero que cofactores, como pasaba en el otro repo.
        A = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]
        r = self.client.post(URL, {'method': 'cramer', 'A': A}, format='json')
        self.assertNotEqual(r.status_code, 200)


class TestMatrixDeterminantValidacion(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_matriz_no_cuadrada_400(self):
        r = self.client.post(URL, {'method': 'cofactors', 'A': [[1.0, 2.0, 3.0]]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_sarrus_sobre_4x4_400_desde_core(self):
        # Error MATEMATICO (Sarrus sólo aplica a 3x3), no de forma: la
        # matriz es cuadrada y bien formada. El 400 tiene que salir del
        # ValueError de core/cramer.py, no del serializer.
        A = [[1.0, 0.0, 0.0, 2.0], [0.0, 1.0, 0.0, 3.0],
             [0.0, 0.0, 1.0, 4.0], [2.0, 3.0, 4.0, 5.0]]
        r = self.client.post(URL, {'method': 'sarrus', 'A': A}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('3x3', r.data['error']['message'])

    def test_metodo_desconocido_400(self):
        r = self.client.post(URL, {'method': 'no_existe', 'A': [[1.0]]}, format='json')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
