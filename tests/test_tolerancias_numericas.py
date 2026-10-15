"""
Tolerancias numéricas: singularidad, rango, determinante, inversa, Cramer y
formato de números chicos.

Los valores esperados están definidos a mano a partir de la matemática
(det(c·B) = c²·det(B), (c·B)⁻¹ = B⁻¹/c, rangos de matrices construidas a
propósito...), no comparando dos funciones del motor entre sí: dos funciones
que comparten el mismo umbral pueden equivocarse juntas, que es justamente el
error que se corrige acá (determinant, is_singular, inverse y Cramer
declaraban singular a 1e-5·I porque todas miraban |det| <= 1e-12).

Criterio de cero bajo prueba: ver el comentario al principio de
core/matrix_tools.py (cota de redondeo por entrada, FACTOR_REDONDEO = 1e4).
"""
import copy
import io
import math
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

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
from core.gauss_jordan import GaussJordanMethod
from utils.EquationFunctions import format_number

B = [[2.0, 1.0], [1.0, 3.0]]                 # det = 5
B_INV = [[0.6, -0.2], [-0.2, 0.4]]           # (1/5)·[[3,-1],[-1,2]]
C3 = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]   # det = 1
ESCALAS = [1e-13, 1e-10, 1e-7, 1e-3, 1.0, 1e3, 1e7, 1e10, 1e13]


def esc(c, M):
    return [[c * x for x in fila] for fila in M]


def diag(*vals):
    n = len(vals)
    return [[vals[i] if i == j else 0.0 for j in range(n)] for i in range(n)]


def cerca(a, b, rel=1e-12):
    return math.isclose(a, b, rel_tol=rel, abs_tol=0.0)


class TestMatricesChicasInvertibles(unittest.TestCase):
    """Problema A: determinantes chicos pero distintos de cero."""

    def _invertible(self, A, det_esperado, inv_esperada):
        n = len(A)
        self.assertTrue(cerca(mt.determinant(A), det_esperado, 1e-9), mt.determinant(A))
        self.assertEqual(mt.rank_of(A), n)
        self.assertIs(mt.is_singular(A), False)
        Ainv, _ = mt.inverse(A)
        for i in range(n):
            for j in range(n):
                if inv_esperada[i][j] == 0.0:
                    self.assertEqual(Ainv[i][j], 0.0)
                else:
                    self.assertTrue(cerca(Ainv[i][j], inv_esperada[i][j], 1e-9), (i, j, Ainv[i][j]))

    def test_ejemplo_1_diag_1e_8(self):
        # Antes: det = 0.0, is_singular True, inverse rechazada.
        self._invertible(diag(1e-8, 1e-8), 1e-16, diag(1e8, 1e8))

    def test_ejemplo_2_1e_5_por_I3(self):
        self._invertible(diag(1e-5, 1e-5, 1e-5), 1e-15, diag(1e5, 1e5, 1e5))

    def test_diagonal_de_escalas_mezcladas(self):
        # Un umbral relativo al MÁXIMO de la matriz rompería este caso.
        self._invertible(diag(1e8, 1e-8), 1.0, diag(1e-8, 1e8))

    def test_filas_de_escalas_muy_distintas(self):
        A = [[1e8, 1e8], [1e-8, 2e-8]]                 # det = 1e8·2e-8 - 1e8·1e-8 = 1
        inv = [[2e-8, -1e8], [-1e-8, 1e8]]             # (1/1)·[[2e-8,-1e8],[-1e-8,1e8]]
        self._invertible(A, 1.0, inv)


class TestInvertiblesEscaladas(unittest.TestCase):
    """det(c·B) = c²·5 y (c·B)⁻¹ = B⁻¹/c para toda escala c ≠ 0."""

    def test_2x2_en_todas_las_escalas(self):
        for c in ESCALAS:
            with self.subTest(c=c):
                A = esc(c, B)
                self.assertTrue(cerca(mt.determinant(A), 5 * c * c, 1e-12))
                self.assertEqual(mt.rank_of(A), 2)
                self.assertIs(mt.is_singular(A), False)
                Ainv, _ = mt.inverse(A)
                for i in range(2):
                    for j in range(2):
                        self.assertTrue(cerca(Ainv[i][j], B_INV[i][j] / c, 1e-9))

    def test_3x3_en_todas_las_escalas(self):
        for c in ESCALAS:
            with self.subTest(c=c):
                A = esc(c, C3)
                self.assertTrue(cerca(mt.determinant(A), c ** 3, 1e-12))
                self.assertEqual(mt.rank_of(A), 3)
                self.assertIs(mt.is_singular(A), False)

    def test_cramer_unica_en_todas_las_escalas(self):
        x0 = [1.0, -2.0]
        for c in ESCALAS:
            with self.subTest(c=c):
                A = esc(c, B)
                b = [sum(a * x for a, x in zip(fila, x0)) for fila in A]   # b = A·x0
                r = CramerMethod(A, b).solve()
                self.assertEqual(r['status'], 'unique')
                for xi, esperado in zip(r['solution'], x0):
                    self.assertTrue(cerca(xi, esperado, 1e-9))
                self.assertTrue(cerca(r['determinant'], 5 * c * c, 1e-12))

    def test_cramer_det_no_representable_da_error_explicito(self):
        # Rango 3, pero det = 1e-330 subdesborda a 0.0: dividir sería 0/0.
        A = diag(1e-110, 1e-110, 1e-110)
        with self.assertRaises(ValueError) as ctx:
            CramerMethod(A, [1.0, 1.0, 1.0]).solve()
        self.assertIn('representable', str(ctx.exception))


class TestSingularesExactas(unittest.TestCase):

    CASOS = [
        # (nombre, A, rango esperado, vector del núcleo esperado (o None))
        ('2x2 filas proporcionales', [[1.0, 2.0], [2.0, 4.0]], 1, [-2.0, 1.0]),
        ('3x3 enteros 1..9', [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], 2, [1.0, -2.0, 1.0]),
        # 0.1..0.9 no son representables en binario: la aritmética directa da
        # det = -2.78e-17. Sigue siendo la matriz singular que se tipeó.
        ('3x3 decimales 0.1..0.9', [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]], 2, [1.0, -2.0, 1.0]),
        ('1e-8 · filas proporcionales', esc(1e-8, [[1.0, 2.0], [2.0, 4.0]]), 1, [-2.0, 1.0]),
        ('1e8 · 1..9', esc(1e8, [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]), 2, [1.0, -2.0, 1.0]),
    ]

    def test_rango_det_singularidad_inversa_y_nucleo(self):
        for nombre, A, rango, nucleo in self.CASOS:
            with self.subTest(caso=nombre):
                n = len(A)
                self.assertEqual(mt.rank_of(A), rango)
                self.assertEqual(mt.determinant(A), 0.0)        # 0 exacto, no ~1e-17
                self.assertIs(mt.is_singular(A), True)
                with self.assertRaises(ValueError):
                    mt.inverse(A)
                v = mt.nullspace_vector(A)
                self.assertIsNotNone(v)
                # proporcional al vector esperado
                k = v[n - 1] / nucleo[n - 1]
                for vi, ei in zip(v, nucleo):
                    self.assertTrue(math.isclose(vi, k * ei, rel_tol=1e-9, abs_tol=1e-12), (v, nucleo))

    def test_sarrus_y_cofactores_explican_el_ruido(self):
        A = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        for metodo, tag in (('calculate_determinant_sarrus', 'sarrus_rounding'),
                            ('calculate_determinant_cofactors', 'cofactor_rounding')):
            with self.subTest(metodo=metodo):
                c = CramerMethod(A, [0.0, 0.0, 0.0])
                c.frame = []
                self.assertEqual(getattr(c, metodo)(A), 0.0)
                pasos = [st for st in c.frame if st['tag'] == tag]
                self.assertEqual(len(pasos), 1)
                self.assertIn('ruido de redondeo', pasos[0]['text'])

    def test_sarrus_no_toca_un_det_chico_legitimo(self):
        A = diag(1e-5, 1e-5, 1e-5)
        c = CramerMethod(A, [0.0, 0.0, 0.0])
        self.assertTrue(cerca(c.calculate_determinant_sarrus(A), 1e-15))
        self.assertNotIn('sarrus_rounding', [st['tag'] for st in c.frame])


class TestCasiSingulares(unittest.TestCase):
    """Criterio documentado: una perturbación relativa de ~1e-11 o más se
    distingue; una de ~1e-13 queda por debajo del redondeo acumulable
    (FACTOR_REDONDEO·n·eps ≈ 4.4e-12 para n = 2) y se trata como singular."""

    def test_el_factor_documentado_es_el_que_rige(self):
        self.assertEqual(mt.FACTOR_REDONDEO, 1e4)

    def test_perturbacion_1e_9_es_invertible(self):
        A = [[1.0, 1.0], [1.0, 1.0 + 1e-9]]
        self.assertEqual(mt.rank_of(A), 2)
        # det = 1e-9 salvo el redondeo de representar 1 + 1e-9 (~1e-16 absoluto)
        self.assertTrue(math.isclose(mt.determinant(A), 1e-9, rel_tol=1e-6))
        mt.inverse(A)   # no levanta

    def test_perturbacion_1e_13_es_numericamente_singular(self):
        A = [[1.0, 1.0], [1.0, 1.0 + 1e-13]]
        self.assertEqual(mt.rank_of(A), 1)
        self.assertEqual(mt.determinant(A), 0.0)
        self.assertIs(mt.is_singular(A), True)
        r = CramerMethod(A, [2.0, 2.0]).solve()
        self.assertEqual(r['status'], 'infinite')


class TestFilasYColumnasNulas(unittest.TestCase):

    def test_casos(self):
        casos = [
            ('fila nula', [[0.0, 0.0], [1.0, 2.0]], 1),
            ('columna nula', [[1.0, 0.0, 2.0], [3.0, 0.0, 4.0], [5.0, 0.0, 6.0]], 2),
            ('matriz nula 3x3', [[0.0] * 3 for _ in range(3)], 0),
            ('fila nula con resto chico', [[0.0, 0.0], [1e-14, 3e-14]], 1),
        ]
        for nombre, A, rango in casos:
            with self.subTest(caso=nombre):
                self.assertEqual(mt.rank_of(A), rango)
                self.assertEqual(mt.determinant(A), 0.0)
                self.assertIs(mt.is_singular(A), True)
                with self.assertRaises(ValueError):
                    mt.inverse(A)

    def test_rectangular_con_columna_chica(self):
        A = [[1.0, 1e-12, 0.0], [2.0, 2e-12, 1.0]]      # columnas 1 y 2 proporcionales
        self.assertEqual(mt.rank_of(A), 2)
        self.assertIsNone(mt.is_singular(A))


class TestRangosDeSistemas(unittest.TestCase):
    """system_ranks: rango(A) y rango([A|b]) sin normalizar b."""

    CASOS = [
        # (nombre, A, b, rango(A), rango([A|b]))
        ('compatible indeterminado', [[1.0, 1.0], [1.0, 1.0]], [1.0, 1.0], 1, 1),
        ('incompatible por 1e-10 en b', [[1.0, 1.0], [1.0, 1.0]], [1.0, 1.0 + 1e-10], 1, 2),
        ('A diminuta, b enorme, única', esc(1e-10, B), [1e10, 0.0], 2, 2),
        ('A diminuta singular, b enorme compatible', esc(1e-10, [[1.0, 1.0], [1.0, 1.0]]), [1e10, 1e10], 1, 1),
        ('A diminuta singular, b enorme incompatible', esc(1e-10, [[1.0, 1.0], [1.0, 1.0]]), [1e10, 2e10], 1, 2),
        ('A = 0, b de magnitudes dispares', [[0.0, 0.0], [0.0, 0.0]], [1e20, 1e-5], 0, 1),
        ('A = 0, b = 0', [[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0], 0, 0),
        ('fila de A diminuta, b normal (0·x = 5 a escala)', [[1.0, 1.0], [1e-10, 1e-10]], [1.0, 5.0], 1, 2),
    ]

    def test_casos(self):
        for nombre, A, b, ra, rab in self.CASOS:
            with self.subTest(caso=nombre):
                self.assertEqual(mt.system_ranks(A, b), (ra, rab))
                self.assertEqual(mt.rank_of(A), ra)

    def test_b_de_otro_largo(self):
        with self.assertRaises(ValueError):
            mt.system_ranks([[1.0, 0.0], [0.0, 1.0]], [1.0])


class TestCramerSingular(unittest.TestCase):
    """La corrección de la primera ronda sigue en pie con el criterio nuevo."""

    def test_A_nula_b_100_sigue_inconsistente(self):
        A = [[0.0] * 3 for _ in range(3)]
        c = CramerMethod(A, [1.0, 0.0, 0.0])
        r = c.solve()
        self.assertEqual(r['status'], 'inconsistent')
        self.assertEqual([st['tag'] for st in c.frame][-2:], ['rank_check', 'inconsistent'])

    def test_singular_decimal_compatible_e_incompatible(self):
        A = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        # b en la imagen de A (columna 1 + columna 2) -> infinitas
        compatible = CramerMethod(A, [0.3, 0.9, 1.5]).solve()
        self.assertEqual(compatible['status'], 'infinite')
        self.assertEqual(compatible['determinant'], 0.0)
        # b fuera de la imagen -> inconsistente
        incompatible = CramerMethod(A, [1.0, 0.0, 0.0]).solve()
        self.assertEqual(incompatible['status'], 'inconsistent')

    def test_det_ruidoso_se_reporta_como_cero_y_se_explica(self):
        A = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        c = CramerMethod(A, [0.3, 0.9, 1.5])
        r = c.solve()
        self.assertEqual(r['determinant'], 0.0)
        primer = c.frame[[st['tag'] for st in c.frame].index('Determinante A')]
        self.assertEqual(primer['det'], '0')
        self.assertIn('ruido de redondeo', primer['text'])
        self.assertEqual(c.determinants_C, [0.0, 0.0, 0.0])

    def test_singular_escalada_compatible(self):
        A = esc(1e-9, [[1.0, 2.0], [2.0, 4.0]])
        r = CramerMethod(A, [3e-9, 6e-9]).solve()
        self.assertEqual(r['status'], 'infinite')


class TestCramerYGaussJordanCoinciden(unittest.TestCase):
    CASOS = [
        ('1e-8·B única', esc(1e-8, B), [3e-8, 4e-8], 'unique'),
        ('1e-5·I3 única', diag(1e-5, 1e-5, 1e-5), [1.0, 1.0, 1.0], 'unique'),
        ('1e7·B única', esc(1e7, B), [1.0, 2.0], 'unique'),
        ('singular decimal infinitas', [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]], [0.3, 0.9, 1.5], 'infinite'),
        ('singular decimal inconsistente', [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]], [1.0, 0.0, 0.0], 'inconsistent'),
        ('A nula, b ≠ 0', [[0.0] * 3 for _ in range(3)], [1.0, 0.0, 0.0], 'inconsistent'),
    ]

    def test_mismo_status(self):
        for nombre, A, b, status in self.CASOS:
            with self.subTest(caso=nombre):
                cr = CramerMethod(copy.deepcopy(A), list(b)).solve()
                gj = GaussJordanMethod(copy.deepcopy(A), list(b))
                gj.run()
                rg = gj.solve_and_log()
                self.assertEqual(cr['status'], status)
                self.assertEqual(rg['status'], status)
                if status == 'unique':
                    for xc, xg in zip(cr['solution'], rg['solution']):
                        self.assertTrue(math.isclose(xc, xg, rel_tol=1e-9))

    def test_gauss_jordan_con_entradas_1e_13(self):
        # Era un expectedFailure: Gauss-Jordan (y gauss_solver) usaban 1e-12
        # absoluto en sus pivotes y con entradas ~1e-13 no encontraban
        # ninguno. Corregido en fix/gauss-consistency: usan el mismo criterio
        # que matrix_tools (CotasDeRedondeo). Ahora es un test normal.
        A, b = esc(1e-13, B), [3e-13, 4e-13]
        self.assertEqual(CramerMethod(copy.deepcopy(A), list(b)).solve()['status'], 'unique')
        gj = GaussJordanMethod(copy.deepcopy(A), list(b))
        gj.run()
        self.assertEqual(gj.solve_and_log()['status'], 'unique')


class TestConsistenciaEntreFunciones(unittest.TestCase):
    """rango < n <=> is_singular <=> inverse levanta, y en ese caso det == 0.0,
    sobre matrices cuyo rango se conoce por construcción. Todas tienen un
    det representable, así que acá también vale la vuelta (det == 0.0 =>
    singular); con det fuera del rango del double NO vale: ver
    tests/test_formato_y_representabilidad.py."""

    CASOS = [
        (diag(1e-8, 1e-8), 2), (diag(1e-5, 1e-5, 1e-5), 3), (esc(1e-13, B), 2), (esc(1e13, C3), 3),
        ([[1e8, 1e8], [1e-8, 2e-8]], 2), ([[1.0, 2.0], [2.0, 4.0]], 1),
        ([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]], 2), ([[0.0] * 2 for _ in range(2)], 0),
        ([[1.0, 1.0], [1.0, 1.0 + 1e-9]], 2),
    ]

    def test_las_cuatro_respuestas_coinciden(self):
        for A, rango in self.CASOS:
            with self.subTest(A=A):
                n = len(A)
                self.assertEqual(mt.rank_of(A), rango)
                singular = rango < n
                self.assertEqual(mt.determinant(A) == 0.0, singular)
                self.assertIs(mt.is_singular(A), singular)
                if singular:
                    with self.assertRaises(ValueError):
                        mt.inverse(A)
                else:
                    mt.inverse(A)

    def test_verificacion_ax_b_y_propiedades_relativas(self):
        # Con 1e-5·I3, A⁻¹ tiene entradas 1e5: el 1e-12 absoluto de antes
        # marcaba FALSO (A⁻¹)⁻¹ = A por puro redondeo.
        A = diag(1e-5, 1e-5, 1e-5)
        _, texto = mt.inverse(A, b=[1e-5, 2e-5, 3e-5])
        self.assertIn('OK (Ax ≈ b)', texto)
        self.assertNotIn('FALSO', texto)


class TestFormatNumber(unittest.TestCase):
    CASOS = [
        (0.0, '0'), (-0.0, '0'),
        (1e-15, '1e-15'), (-1e-15, '-1e-15'), (1e-7, '1e-7'), (2.5e-10, '2.5e-10'), (1e-16, '1e-16'),
        (2.0, '2'), (-7.0, '-7'), (1.9999999999999998, '≈2'), (123.0, '123'),
        (0.5, '1/2'), (-0.5, '-1/2'), (1 / 3, '1/3'), (-2 / 7, '-2/7'), (0.30000000000000004, '≈3/10'),
        (0.001, '1/1000'), (0.0015, '3/2000'),
        (math.pi, '≈3.141592654'), (1e20, '1e20'), (-3.5e-12, '-3.5e-12'),
        (float('inf'), 'inf'), (float('-inf'), '-inf'),
    ]

    def test_casos(self):
        for valor, esperado in self.CASOS:
            with self.subTest(valor=valor):
                self.assertEqual(format_number(valor), esperado)

    def test_nan(self):
        self.assertEqual(format_number(float('nan')), 'nan')

    def test_ningun_valor_finito_no_nulo_se_muestra_como_cero(self):
        for e in range(-300, 300, 7):
            for s in (1.0, -1.0, 3.7):
                v = s * 10.0 ** e
                with self.subTest(v=v):
                    self.assertNotEqual(format_number(v), '0')

    def test_enteros_python_siguen_funcionando(self):
        self.assertEqual(format_number(5), '5')
        self.assertEqual(format_number(-12), '-12')


class TestApiYCli(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_properties_1e_5_I3(self):
        r = self.client.post('/api/v1/matrix/properties', {'A': diag(1e-5, 1e-5, 1e-5)}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['result']['rank'], 3)
        self.assertIs(r.data['result']['is_singular'], False)
        self.assertIsNone(r.data['result']['nullspace'])

    def test_operate_inverse_diag_1e_8(self):
        r = self.client.post('/api/v1/matrix/operate', {'operation': 'inverse', 'A': diag(1e-8, 1e-8)}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        M = r.data['result']['matrix']
        self.assertTrue(cerca(M[0][0], 1e8, 1e-9) and cerca(M[1][1], 1e8, 1e-9))

    def test_determinant_sarrus_singular_decimal_da_cero(self):
        A = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        r = self.client.post('/api/v1/matrix/determinant', {'method': 'sarrus', 'A': A}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['result']['determinant'], 0.0)
        self.assertEqual(r.data['result']['determinant_pretty'], '0')

    def test_determinant_cofactores_chico_legitimo(self):
        r = self.client.post('/api/v1/matrix/determinant', {'method': 'cofactors', 'A': diag(1e-8, 1e-8)}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertTrue(cerca(r.data['result']['determinant'], 1e-16))
        # 1e-8·1e-8 en coma flotante da 1.0000000000000001e-16, no 1e-16
        # exacto: se muestra marcado como aproximación.
        self.assertEqual(r.data['result']['determinant_pretty'], '≈1e-16')

    def test_reduce_cramer_1e_5_I3(self):
        r = self.client.post('/api/v1/matrix/reduce', {'method': 'cramer', 'A': diag(1e-5, 1e-5, 1e-5), 'b': [1.0, 2.0, 3.0]}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        s = r.data['summary']
        self.assertEqual(s['status'], 'unique')
        self.assertIs(s['is_singular'], False)
        for xi, esperado in zip(s['solution'], [1e5, 2e5, 3e5]):
            self.assertTrue(cerca(xi, esperado, 1e-9))
        self.assertEqual(s['determinant_pretty'], '≈1e-15')   # calculado: 1.0000000000000002e-15
        # los n+1 determinantes y el mismo shape de siempre
        self.assertEqual(len(r.data['result']['determinants']), 4)
        self.assertEqual(set(s), {'status', 'solution_type', 'solution', 'basic_vars', 'free_vars',
                                  'variables', 'determinant', 'determinant_pretty', 'is_singular'})

    def test_reduce_cramer_determinantes_coinciden_con_los_pasos(self):
        A = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        r = self.client.post('/api/v1/matrix/reduce', {'method': 'cramer', 'A': A, 'b': [0.3, 0.9, 1.5]}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual([d['value'] for d in r.data['result']['determinants']], [0.0, 0.0, 0.0, 0.0])
        self.assertEqual(r.data['summary']['status'], 'infinite')

    def test_reduce_cramer_det_no_representable_400(self):
        r = self.client.post('/api/v1/matrix/reduce', {'method': 'cramer', 'A': diag(1e-110, 1e-110, 1e-110), 'b': [1.0, 1.0, 1.0]}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_cli_cramer_1e_5_I3(self):
        from cli.method_runners import run_cramer
        entradas = iter(['3', '3', '0.00001 0 0', '1', '0 0.00001 0', '1', '0 0 0.00001', '1'])
        salida = io.StringIO()
        with mock.patch('builtins.input', lambda *a, **k: next(entradas)), redirect_stdout(salida):
            run_cramer()
        texto = salida.getvalue()
        self.assertIn('Status: unique', texto)
        self.assertIn('100000', texto)


class TestNoMutaLasEntradas(unittest.TestCase):

    def test_ninguna_funcion_modifica_A_ni_b(self):
        A = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.95]]
        b = [1.0, 2.0, 3.0]
        A0, b0 = copy.deepcopy(A), list(b)
        mt.rank_of(A); mt.determinant(A); mt.is_singular(A); mt.nullspace_vector(A)
        mt.system_ranks(A, b); mt.inverse(A, b=b); mt.verify_inverse_props(A)
        c = CramerMethod(A, b)
        c.solve(); c.calculate_determinant_sarrus(A); c.calculate_determinant_cofactors(A)
        self.assertEqual(A, A0)
        self.assertEqual(b, b0)
        self.assertEqual(c.matrix_A, A0)
        self.assertEqual(c.vector_b, b0)


if __name__ == '__main__':
    unittest.main()
