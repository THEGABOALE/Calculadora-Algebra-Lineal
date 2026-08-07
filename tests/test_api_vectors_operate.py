"""
Tests de POST /api/v1/vectors/operate con rest_framework.test.APIClient.

Mismo criterio que los demás tests de la API: sin django.test.TestCase, sin
base de datos.

TestVectorOperateParidad cubre las 6 operaciones contra core/vector.Vector
llamado directo. 'dot' se verifica aparte (TestVectorOperateDot) porque su
'result' tiene otro shape -- escalar, no vector -- y no comparte código con
las otras cinco.
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

from core.vector import Vector

URL = '/api/v1/vectors/operate'

U = [1.0, 2.0, 3.0]
V = [4.0, -1.0, 2.0]
W = [0.5, 1.0, -2.0]


class TestVectorOperateParidad(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_add(self):
        r = self.client.post(URL, {'operation': 'add', 'vectors': {'u': U, 'v': V}}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['result']['vector'], Vector(U).add(Vector(V)).data)

    def test_sub(self):
        r = self.client.post(URL, {'operation': 'sub', 'vectors': {'u': U, 'v': V}}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['result']['vector'], Vector(U).sub(Vector(V)).data)

    def test_escalar(self):
        r = self.client.post(URL, {'operation': 'escalar', 'vectors': {'u': U}, 'scalars': {'c': 2.5}}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['result']['vector'], Vector(U).scale(2.5).data)

    def test_comb2(self):
        r = self.client.post(URL, {
            'operation': 'comb2', 'vectors': {'u': U, 'v': V}, 'scalars': {'c': 2.0, 'd': -1.5},
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        esperado = Vector(U).scale(2.0).add(Vector(V).scale(-1.5)).data
        for va, vd in zip(r.data['result']['vector'], esperado):
            self.assertAlmostEqual(va, vd, places=9)

    def test_comb3(self):
        r = self.client.post(URL, {
            'operation': 'comb3', 'vectors': {'u': U, 'v': V, 'w': W}, 'scalars': {'c': 3.0, 'd': 1.0},
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        esperado = Vector(U).add(Vector(V).scale(3.0)).add(Vector(W).scale(1.0)).data
        for va, vd in zip(r.data['result']['vector'], esperado):
            self.assertAlmostEqual(va, vd, places=9)


class TestVectorOperateDot(unittest.TestCase):
    """dot devuelve un escalar, no un vector: 'result' tiene otro shape que
    las cinco operaciones de arriba, y las claves del request son distintas
    (vectors.v/vectors.w, no vectors.u/vectors.v)."""

    def setUp(self):
        self.client = APIClient()

    def test_dot_usa_las_claves_v_y_w(self):
        # Así arma el request AlgebraicMethods.tsx: payload.vectors = {v: u, w: v}.
        r = self.client.post(URL, {'operation': 'dot', 'vectors': {'v': U, 'w': V}}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['result']['scalar'], Vector(U).dot(Vector(V)), places=9)

    def test_dot_con_claves_u_v_da_400(self):
        # Si alguien manda las claves "normales" (u, v) en vez de (v, w),
        # el serializer debe rechazarlo -- no adivinar cuál vector es cuál.
        r = self.client.post(URL, {'operation': 'dot', 'vectors': {'u': U, 'v': V}}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_dot_result_no_tiene_clave_vector(self):
        r = self.client.post(URL, {'operation': 'dot', 'vectors': {'v': U, 'w': V}}, format='json')
        self.assertNotIn('vector', r.data['result'])
        self.assertIn('scalar', r.data['result'])
        self.assertIn('scalar_pretty', r.data['result'])

    def test_dot_no_trae_diagram(self):
        # Las otras cinco sí traen 'diagram'; dot no, porque no hay flechas
        # que dibujar para un escalar.
        r = self.client.post(URL, {'operation': 'dot', 'vectors': {'v': U, 'w': V}}, format='json')
        self.assertNotIn('diagram', r.data)


class TestVectorOperateDiagram(unittest.TestCase):
    """diagram: {"vectors": [{label, from, to, emphasis?}]}, la forma que
    ya trae el contrato portado. No hay componente del frontend que lo
    consuma hoy (verificado), pero la forma tiene que ser exacta."""

    def setUp(self):
        self.client = APIClient()

    def test_shape_para_add(self):
        r = self.client.post(URL, {'operation': 'add', 'vectors': {'u': U, 'v': V}}, format='json')
        vectores = r.data['diagram']['vectors']
        self.assertEqual(vectores[0], {'label': 'u', 'from': [0, 0, 0], 'to': U})
        self.assertEqual(vectores[1], {'label': 'v', 'from': [0, 0, 0], 'to': V})
        self.assertEqual(vectores[-1]['label'], 'resultado')
        self.assertTrue(vectores[-1]['emphasis'])

    def test_escalar_incluye_el_vector_escalado(self):
        r = self.client.post(URL, {'operation': 'escalar', 'vectors': {'u': U}, 'scalars': {'c': 2.0}}, format='json')
        etiquetas = [v['label'] for v in r.data['diagram']['vectors']]
        self.assertIn('2·u', etiquetas)


class TestVectorOperateValidacion(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_operacion_desconocida_400(self):
        r = self.client.post(URL, {'operation': 'no_existe', 'vectors': {'u': U}}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_add_dimensiones_incompatibles_400(self):
        r = self.client.post(URL, {'operation': 'add', 'vectors': {'u': [1.0, 2.0], 'v': [1.0, 2.0, 3.0]}}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_escalar_sin_c_400(self):
        r = self.client.post(URL, {'operation': 'escalar', 'vectors': {'u': U}}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_comb3_sin_w_400(self):
        r = self.client.post(URL, {
            'operation': 'comb3', 'vectors': {'u': U, 'v': V}, 'scalars': {'c': 1.0, 'd': 1.0},
        }, format='json')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
