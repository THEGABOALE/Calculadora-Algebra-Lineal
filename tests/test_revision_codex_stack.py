"""
Regresiones de los cuatro comentarios de Codex abiertos en el stack
(PR #5: inversa y numerador de Cramer; PR #6: multiplicador de Gauss y
det(Aᵢ) no representable), más el caso de Codex del PR #4.

Valores esperados matemáticos, no de otra función del motor.
"""
import copy
import math
import os
import sys
import unittest
import warnings

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

from core import matrix_tools as mt
from core.cramer import CramerMethod
from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.system_solver.gauss_solver import solve_system_direct


def gauss(A, b):
    g = GaussMethod(copy.deepcopy(A), list(b))
    g.gauss_method()
    return g, g.solve_and_log()


def gj(A, b):
    g = GaussJordanMethod(copy.deepcopy(A), list(b))
    g.run()
    return g, g.solve_and_log()


class TestComentario1InversaCasiSingular(unittest.TestCase):
    """PR #5: inverse() usaba tau(n, 2n) para las columnas de A y rank_of
    tau(n, n); una matriz de rango completo cerca del umbral era rechazada."""

    def test_rango_completo_implica_inversa(self):
        for d in (1e-9, 1e-10, 1e-11):
            A = [[1.0, 1.0], [1.0, 1.0 + d]]
            with self.subTest(d=d):
                self.assertEqual(mt.rank_of(A), 2)
                self.assertIs(mt.is_singular(A), False)
                Ainv, _ = mt.inverse(A, check_props=False)
                # A·A⁻¹ = I, con el error esperable para cond(A) ~ 4/d
                for i in range(2):
                    for j in range(2):
                        v = sum(A[i][k] * Ainv[k][j] for k in range(2))
                        self.assertAlmostEqual(v, 1.0 if i == j else 0.0, delta=1e5 * d * 1e-6 + 1e-4)

    def test_singular_por_el_mismo_criterio_sigue_rechazada(self):
        A = [[1.0, 1.0], [1.0, 1.0 + 1e-13]]
        self.assertIs(mt.is_singular(A), True)
        with self.assertRaises(ValueError):
            mt.inverse(A)

    def test_singularidad_e_inversa_coinciden_en_la_zona_del_umbral(self):
        for k in range(0, 60):
            d = 10.0 ** (-10 - k / 20.0)                   # 1e-10 .. ~1e-13
            A = [[1.0, 1.0], [1.0, 1.0 + d]]
            with self.subTest(d=d):
                if mt.is_singular(A):
                    with self.assertRaises(ValueError):
                        mt.inverse(A, check_props=False)
                else:
                    mt.inverse(A, check_props=False)


class TestComentario2NumeradorDeCramer(unittest.TestCase):
    """PR #5: det(A₁) = 1e-300 es representable pero la multiplicación
    directa (1e-300·1e-100)·1e100 subdesbordaba; en la rama de tolerancias
    salía [0,0,0]. Corregido en la ronda 3 (producto_sin_desborde)."""

    def test_solucion_correcta(self):
        A = [[1e-100, 0.0, 0.0], [0.0, 1e-100, 0.0], [0.0, 0.0, 1e100]]
        r = CramerMethod(copy.deepcopy(A), [1e-300, 0.0, 0.0]).solve()
        self.assertEqual(r['status'], 'unique')
        self.assertTrue(math.isclose(r['solution'][0], 1e-200, rel_tol=1e-12))
        self.assertEqual(r['solution'][1:], [0.0, 0.0])


class TestComentario3MultiplicadorDeEliminacion(unittest.TestCase):
    """PR #6: entrada/pivote = 1e-300/1e300 subdesbordaba a 0; la fila
    quedaba [0 | 1e-300] y el sistema compatible salía 'inconsistent'."""

    CASOS = [
        ([[1e300], [1e-300]], [1e300, 1e-300], [1.0]),
        ([[1e300, 1e300], [1e-300, 2e-300]], [2e300, 3e-300], [1.0, 1.0]),
        ([[1e300, 0.0], [1e-300, 1.0]], [1e300, 1.0 + 1e-300], [1.0, 1.0]),
    ]

    def test_gauss_gauss_jordan_y_directo(self):
        for A, b, x in self.CASOS:
            for nombre, resolver in (('gauss', lambda: gauss(A, b)[1]),
                                     ('gauss-jordan', lambda: gj(A, b)[1]),
                                     ('directo', lambda: solve_system_direct(A, b))):
                with self.subTest(metodo=nombre, A=A):
                    r = resolver()
                    self.assertEqual(r['status'], 'unique')
                    for xi, esperado in zip(r['solution'], x):
                        self.assertTrue(math.isclose(xi, esperado, rel_tol=1e-12), (xi, esperado))

    def test_incompatible_a_la_misma_escala_sigue_detectado(self):
        A, b = [[1e300], [1e-300]], [1e300, 2e-300]          # x = 1 y x = 2
        for resolver in (lambda: gauss(A, b)[1], lambda: gj(A, b)[1], lambda: solve_system_direct(A, b)):
            self.assertEqual(resolver()['status'], 'inconsistent')

    def test_el_paso_muestra_el_multiplicador_como_cociente(self):
        g, _ = gauss([[1e300], [1e-300]], [1e300, 1e-300])
        elim = [st['text'] for st in g.frame if st['tag'] == 'elim']
        self.assertEqual(len(elim), 1)
        self.assertIn('1e-300/1e300', elim[0])


class TestComentario4NumeradorNoRepresentable(unittest.TestCase):
    """PR #6: det(A₃) = 1e-330 no es representable; solve() devolvía
    x₃ = 0 en silencio (correcto: 1e-230). Ahora: error explícito, igual
    que cuando det(A) no es representable."""

    def test_error_explicito_en_vez_de_cero(self):
        A = [[1e-200, 0.0, 0.0], [0.0, 1e-200, 0.0], [0.0, 0.0, 1e300]]
        b = [1e-200, 1e-200, 1e70]
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            with self.assertRaises(ValueError) as ctx:
                CramerMethod(copy.deepcopy(A), b).solve()
        self.assertIn('det(A₃)', str(ctx.exception))
        self.assertIn('no es representable', str(ctx.exception))

    def test_api_responde_400(self):
        r = APIClient().post('/api/v1/matrix/reduce', {
            'method': 'cramer', 'A': [[1e-200, 0.0, 0.0], [0.0, 1e-200, 0.0], [0.0, 0.0, 1e300]],
            'b': [1e-200, 1e-200, 1e70]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_gauss_jordan_resuelve_el_mismo_sistema(self):
        A = [[1e-200, 0.0, 0.0], [0.0, 1e-200, 0.0], [0.0, 0.0, 1e300]]
        _, r = gj(A, [1e-200, 1e-200, 1e70])
        self.assertEqual(r['status'], 'unique')
        self.assertTrue(math.isclose(r['solution'][2], 1e-230, rel_tol=1e-12))

    def test_numerador_cero_legitimo_no_es_error(self):
        # A₂ singular (columna 2 reemplazada por b, que es múltiplo de la 1):
        # det(A₂) = 0 es dato, x₂ = 0.
        A = [[2.0, 1.0], [1.0, 3.0]]
        r = CramerMethod(copy.deepcopy(A), [2.0, 1.0]).solve()
        self.assertEqual(r['solution'], [1.0, 0.0])


class TestCasoCodexPR4SigueBien(unittest.TestCase):

    def test_infinitas(self):
        A, b = [[1e-13, 0.0], [0.0, 0.0]], [1.0, 0.0]
        self.assertEqual(CramerMethod(copy.deepcopy(A), list(b)).solve()['status'], 'infinite')
        self.assertEqual(gauss(A, b)[1]['status'], 'infinite')
        self.assertEqual(gj(A, b)[1]['status'], 'infinite')
        self.assertEqual(mt.system_ranks(A, b), (1, 1))


if __name__ == '__main__':
    unittest.main()
