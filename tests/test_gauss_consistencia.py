"""
Consistencia de Gauss y Gauss-Jordan con el criterio numérico de
core/matrix_tools.py (rama fix/gauss-consistency).

Los resultados esperados se construyen a mano, no con el motor: cada sistema
se arma a partir de una solución conocida x0 (b = A·x0 en racionales exactos)
o de una relación de dependencia conocida entre filas, y el rango esperado es
el de la construcción.

Errores que fija:
- Gauss / Gauss-Jordan / gauss_solver usaban 1e-12 / 1e-13 absolutos:
  "infinitas" para sistemas invertibles ~1e-13, "compatible" para 0 = 1e-13,
  "incompatible" para sistemas compatibles ~1e8 (el ruido pasaba por dato).
- GaussMethod.gauss_method() salía antes de eliminar si [A|b] era cuadrada
  y tenía filas/columnas nulas o repetidas: 3x2 con solución única salía
  "infinitas". Y registraba como "Determinante" el producto de la diagonal
  de [A|b] (y nunca det(A) para A cuadrada).
- solve_system_direct() reventaba con TypeError (typing.List) y leía el
  pivote de aug[row][row].
- print_equation() ocultaba coeficientes < 1e-12, perdía el signo del primer
  término y escribía " = 1" para una fila nula.
"""
import copy
import io
import math
import os
import sys
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
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
from core.gauss import GaussMethod
from core.gauss_jordan import GaussJordanMethod
from core.system_solver.gauss_solver import solve_system_direct
from utils.printMethods import print_equation


# --------------------------------------------------------------------------
# Construcción de casos con resultado conocido
# --------------------------------------------------------------------------
def producto(A, x):
    """A·x en racionales exactos, devuelto en float."""
    return [float(sum(Fraction(a) * Fraction(xi) for a, xi in zip(fila, x))) for fila in A]


def esc(k, M):
    return [[k * v for v in fila] for fila in M]


class Caso:
    def __init__(self, nombre, A, b, status, rango_a, rango_ab, x0=None):
        self.nombre, self.A, self.b = nombre, A, b
        self.status, self.rango_a, self.rango_ab, self.x0 = status, rango_a, rango_ab, x0


B2 = [[2.0, 1.0], [1.0, 3.0]]
B3 = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]]
SING3 = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]        # fila3 = 2·fila2 - fila1

CASOS = [
    # --- solución única --------------------------------------------------
    Caso('2x2 única', B2, producto(B2, [1, -2]), 'unique', 2, 2, [1, -2]),
    Caso('3x3 única', B3, producto(B3, [3, -1, 2]), 'unique', 3, 3, [3, -1, 2]),
    Caso('3x3 única fraccionaria', B3, producto(B3, [Fraction(1, 3), Fraction(-2, 7), 5]), 'unique', 3, 3,
         [Fraction(1, 3), Fraction(-2, 7), 5]),
    Caso('2x2 ~1e-13 (era el expectedFailure)', esc(1e-13, B2), producto(esc(1e-13, B2), [1, 1]), 'unique', 2, 2, [1, 1]),
    Caso('3x3 ~1e-13', esc(1e-13, B3), producto(esc(1e-13, B3), [1, 2, -1]), 'unique', 3, 3, [1, 2, -1]),
    Caso('pivote nulo: requiere intercambio', [[0.0, 1.0], [1.0, 0.0]], [2.0, 3.0], 'unique', 2, 2, [3, 2]),
    Caso('pivote nulo 3x3', [[0.0, 2.0, 1.0], [1.0, 1.0, 1.0], [2.0, 1.0, 0.0]],
         producto([[0, 2, 1], [1, 1, 1], [2, 1, 0]], [1, 1, 1]), 'unique', 3, 3, [1, 1, 1]),
    Caso('escalas mezcladas diag(1e8, 1e-8)', [[1e8, 0.0], [0.0, 1e-8]], [2e8, 3e-8], 'unique', 2, 2, [2, 3]),
    Caso('filas de escala 1e8 y 1e-8', [[1e8, 1e8], [1e-8, 2e-8]], producto([[1e8, 1e8], [1e-8, 2e-8]], [1, 1]),
         'unique', 2, 2, [1, 1]),
    Caso('A ~1e-10, b ~1', esc(1e-10, B2), [1.0, 0.0], 'unique', 2, 2,
         [Fraction(3, 5) * 10 ** 10, Fraction(-1, 5) * 10 ** 10]),
    Caso('3x2 sobredeterminado con filas repetidas', [[1.0, 1.0], [1.0, 1.0], [1.0, 2.0]], [2.0, 2.0, 3.0],
         'unique', 2, 2, [1, 1]),
    Caso('3x2 homogéneo', [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [0.0, 0.0, 0.0], 'unique', 2, 2, [0, 0]),
    # --- infinitas -------------------------------------------------------
    Caso('3x3 singular, b en la imagen', SING3, producto(SING3, [1, 1, 1]), 'infinite', 2, 2),
    Caso('1e8 · singular, b en la imagen', esc(1e8, SING3), producto(esc(1e8, SING3), [1, 1, 1]), 'infinite', 2, 2),
    Caso('decimales 0.1..0.9, b en la imagen', esc(0.1, SING3), [0.6, 1.5, 2.4], 'infinite', 2, 2),
    Caso('columna sin pivote (2x3)', [[1.0, 2.0, 3.0], [0.0, 0.0, 1.0]], [1.0, 2.0], 'infinite', 2, 2),
    Caso('columnas repetidas', [[1.0, 1.0, 2.0], [3.0, 3.0, 1.0], [0.0, 0.0, 5.0]], [4.0, 7.0, 5.0], 'infinite', 2, 2),
    Caso('A = 0, b = 0', [[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0], 'infinite', 0, 0),
    # --- incompatibles ---------------------------------------------------
    Caso('3x3 singular, b fuera de la imagen', SING3, [1.0, 1.0, 0.0], 'inconsistent', 2, 3),
    Caso('A ~1, b ~1e-13: 0 = 1e-13', [[1.0, 1.0], [1.0, 1.0]], [0.0, 1e-13], 'inconsistent', 1, 2),
    Caso('A = 0, b ≠ 0', [[0.0, 0.0, 0.0]] * 3, [1.0, 0.0, 0.0], 'inconsistent', 0, 1),
    Caso('3x2 incompatible', [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [1.0, 1.0, 3.0], 'inconsistent', 2, 3),
    Caso('decimales 0.1..0.9, b fuera', esc(0.1, SING3), [1.0, 0.0, 0.0], 'inconsistent', 2, 3),
]


def resolver_gauss(A, b):
    g = GaussMethod(copy.deepcopy(A), list(b))
    g.gauss_method()
    return g, g.solve_and_log()


def resolver_gj(A, b):
    g = GaussJordanMethod(copy.deepcopy(A), list(b))
    g.run()
    return g, g.solve_and_log()


def residuo_ok(A, x, b, rel=1e-9):
    """|(Ax)_i - b_i| <= rel·(Σ|a_ij x_j| + |b_i|) en cada fila."""
    for fila, bi in zip(A, b):
        ax = sum(a * xi for a, xi in zip(fila, x))
        if abs(ax - bi) > rel * (sum(abs(a * xi) for a, xi in zip(fila, x)) + abs(bi)):
            return False
    return True


# --------------------------------------------------------------------------
class TestClasificacion(unittest.TestCase):

    def _verificar(self, metodo, resolver):
        for c in CASOS:
            with self.subTest(metodo=metodo, caso=c.nombre):
                solver, r = resolver(c.A, c.b)
                self.assertEqual(r['status'], c.status)
                self.assertEqual(r['rank'], c.rango_a)
                n = len(c.A[0])
                self.assertEqual(len(r['basic_vars']) + len(r['free_vars']), n)
                self.assertEqual(len(r['free_vars']), n - c.rango_a)
                if c.status == 'inconsistent':
                    self.assertIsNone(r['solution'])
                    continue
                self.assertTrue(residuo_ok(c.A, r['solution'], c.b), r['solution'])
                if c.x0 is not None:
                    for xi, esperado in zip(r['solution'], c.x0):
                        self.assertTrue(math.isclose(xi, float(esperado), rel_tol=1e-9, abs_tol=1e-300),
                                        (xi, float(esperado)))

    def test_gauss(self):
        self._verificar('gauss', resolver_gauss)

    def test_gauss_jordan(self):
        self._verificar('gauss-jordan', resolver_gj)

    def test_solve_system_direct(self):
        self._verificar('solve_system_direct', lambda A, b: (None, solve_system_direct(A, b)))

    def test_rangos_de_A_y_de_Ab(self):
        for c in CASOS:
            with self.subTest(caso=c.nombre):
                self.assertEqual(mt.system_ranks(c.A, c.b), (c.rango_a, c.rango_ab))

    def test_variables_basicas_y_libres_de_la_columna_sin_pivote(self):
        A, b = [[1.0, 2.0, 3.0], [0.0, 0.0, 1.0]], [1.0, 2.0]
        for resolver in (resolver_gauss, resolver_gj):
            _, r = resolver(A, b)
            self.assertEqual(r['basic_vars'], [0, 2])
            self.assertEqual(r['free_vars'], [1])
            # x2 = 0 (libre); x3 = 2; x1 = 1 - 3·2 = -5
            self.assertEqual(r['solution'], [-5.0, 0.0, 2.0])


class TestConsistenciaEntreMetodos(unittest.TestCase):

    def test_gauss_gj_cramer_y_rangos_coinciden(self):
        for c in CASOS:
            with self.subTest(caso=c.nombre):
                _, rg = resolver_gauss(c.A, c.b)
                _, rj = resolver_gj(c.A, c.b)
                self.assertEqual(rg['status'], rj['status'])
                self.assertEqual(rg['basic_vars'], rj['basic_vars'])
                self.assertEqual(rg['free_vars'], rj['free_vars'])
                if len(c.A) == len(c.A[0]):
                    self.assertEqual(CramerMethod(copy.deepcopy(c.A), list(c.b)).solve()['status'], rg['status'])
                if rg['status'] == 'unique':
                    for xg, xj in zip(rg['solution'], rj['solution']):
                        self.assertTrue(math.isclose(xg, xj, rel_tol=1e-9, abs_tol=1e-300))


class TestApiCoincideConElMotor(unittest.TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_reduce(self):
        for c in CASOS:
            for metodo, resolver in (('gauss', resolver_gauss), ('gauss-jordan', resolver_gj)):
                with self.subTest(caso=c.nombre, metodo=metodo):
                    r = self.client.post('/api/v1/matrix/reduce', {'method': metodo, 'A': c.A, 'b': c.b}, format='json')
                    self.assertEqual(r.status_code, 200, r.data)
                    s = r.data['summary']
                    _, motor = resolver(c.A, c.b)
                    self.assertEqual(s['status'], c.status)
                    self.assertEqual(s['status'], motor['status'])
                    self.assertEqual(s['ranks'], {'rankA': c.rango_a, 'rankAb': c.rango_ab})
                    self.assertEqual(s['basic_vars'], motor['basic_vars'])
                    self.assertEqual(s['free_vars'], motor['free_vars'])
                    if c.status == 'inconsistent':
                        self.assertIsNone(s['solution'])
                    else:
                        for xa, xm in zip(s['solution'], motor['solution']):
                            self.assertEqual(xa, xm)


class TestPasosRegistrados(unittest.TestCase):

    def test_gauss_deja_forma_escalonada_y_el_frame_termina_en_ella(self):
        for c in CASOS:
            with self.subTest(caso=c.nombre):
                g, r = resolver_gauss(c.A, c.b)
                U = g.matriz
                pivotes = g.pivots
                self.assertEqual(len(pivotes), c.rango_a)
                # columnas de pivote estrictamente crecientes, ceros EXACTOS debajo
                cols = [col for _, col in pivotes]
                self.assertEqual(cols, sorted(set(cols)))
                for fila, col in pivotes:
                    self.assertNotEqual(U[fila][col], 0.0)
                    for k in range(fila + 1, len(U)):
                        self.assertEqual(U[k][col], 0.0)
                # filas sin pivote: parte A nula exacta
                for k in range(len(pivotes), len(U)):
                    self.assertTrue(all(v == 0.0 for v in U[k][:-1]))
                upper = [st for st in g.frame if st['tag'] == 'upper']
                self.assertEqual(len(upper), 1)
                self.assertEqual(upper[0]['matrix'], U)
                self.assertEqual(sum(1 for st in g.frame if st['tag'] == 'pivot'), c.rango_a)

    def test_gauss_jordan_deja_rref(self):
        for c in CASOS:
            with self.subTest(caso=c.nombre):
                g, r = resolver_gj(c.A, c.b)
                R = g.matriz
                for fila, col in g.pivots:
                    self.assertEqual(R[fila][col], 1.0)
                    for k in range(len(R)):
                        if k != fila:
                            self.assertEqual(R[k][col], 0.0)
                rref = [st for st in g.frame if st['tag'] == 'rref']
                self.assertEqual(rref[-1]['matrix'], R)

    def test_el_intercambio_de_filas_queda_registrado(self):
        g, _ = resolver_gauss([[0.0, 1.0], [1.0, 0.0]], [2.0, 3.0])
        self.assertIn('swap_rows', [st['tag'] for st in g.frame])
        j, _ = resolver_gj([[0.0, 1.0], [1.0, 0.0]], [2.0, 3.0])
        self.assertIn('swap_rows', [st['tag'] for st in j.frame])


class TestGaussYaNoCortaLaEliminacion(unittest.TestCase):

    def test_3x2_con_filas_repetidas_se_elimina_completo(self):
        g, r = resolver_gauss([[1.0, 1.0], [1.0, 1.0], [1.0, 2.0]], [2.0, 2.0, 3.0])
        tags = [st['tag'] for st in g.frame]
        self.assertIn('elim', tags)
        self.assertIn('upper', tags)
        self.assertEqual(r['status'], 'unique')

    def test_singular_cuadrada_registra_el_atajo_y_sigue(self):
        # Filas iguales => det(A) = 0, pero el sistema puede ser cualquiera de
        # los dos: la eliminación completa los distingue.
        for b, esperado in (([1.0, 1.0], 'infinite'), ([1.0, 2.0], 'inconsistent')):
            with self.subTest(b=b):
                g, r = resolver_gauss([[1.0, 2.0], [1.0, 2.0]], b)
                tags = [st['tag'] for st in g.frame]
                self.assertIn('singular', tags)
                self.assertIn('upper', tags)
                self.assertGreater(tags.index('upper'), tags.index('singular'))
                self.assertEqual(r['status'], esperado)

    def test_determinante_solo_para_A_cuadrada(self):
        g, _ = resolver_gauss(B3, producto(B3, [1, 1, 1]))
        dets = [st for st in g.frame if st['tag'] == 'det']
        self.assertEqual(len(dets), 1)
        self.assertTrue(math.isclose(g.determinante, -1.0, rel_tol=1e-12))   # det(B3) = -1
        g2, _ = resolver_gauss([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], [1.0, 1.0, 1.0])
        self.assertEqual([st for st in g2.frame if st['tag'] == 'det'], [])
        self.assertIsNone(g2.determinante)

    def test_determinante_singular_es_cero_y_signo_de_intercambio(self):
        g, _ = resolver_gauss(SING3, [1.0, 1.0, 1.0])
        self.assertEqual(g.determinante, 0.0)
        g2, _ = resolver_gauss([[0.0, 1.0], [1.0, 0.0]], [1.0, 1.0])
        self.assertEqual(g2.determinante, -1.0)

    def test_fordward_elimination_aug_es_la_misma_eliminacion(self):
        A, b = esc(1e-13, B2), producto(esc(1e-13, B2), [1, 1])
        g = GaussMethod(copy.deepcopy(A), list(b))
        U, piv = g.fordward_elimination_aug()
        self.assertEqual(piv, [(0, 0), (1, 1)])


class TestHomogeneidad(unittest.TestCase):

    def test_b_chico_no_es_homogeneo(self):
        self.assertFalse(GaussJordanMethod([[1.0, 0.0], [0.0, 1.0]], [1e-13, 0.0]).is_homogeneous)
        self.assertTrue(GaussJordanMethod([[1.0, 0.0], [0.0, 1.0]], [0.0, -0.0]).is_homogeneous)


class TestSolveSystemDirect(unittest.TestCase):

    def test_pivote_en_columna_distinta_de_la_fila(self):
        # Antes: aug[row][row] tomaba la entrada equivocada cuando la primera
        # columna no tiene pivote. x2 + x3 = 1, 2x2 + 3x3 = 1 -> x3 = -1, x2 = 2.
        r = solve_system_direct([[0.0, 1.0, 1.0], [0.0, 2.0, 3.0]], [1.0, 1.0])
        self.assertEqual(r['status'], 'infinite')
        self.assertEqual(r['free_vars'], [0])
        self.assertEqual(r['solution'], [0.0, 2.0, -1.0])

    def test_vacio_y_errores_de_forma(self):
        self.assertEqual(solve_system_direct([], [])['status'], 'unique')
        with self.assertRaises(ValueError):
            solve_system_direct([[1.0, 2.0]], [1.0, 2.0])
        with self.assertRaises(ValueError):
            solve_system_direct([[1.0, 2.0], [1.0]], [1.0, 2.0])

    def test_no_muta_la_entrada(self):
        A, b = [[0.0, 1.0], [1.0, 0.0]], [2.0, 3.0]
        A0, b0 = copy.deepcopy(A), list(b)
        solve_system_direct(A, b)
        self.assertEqual((A, b), (A0, b0))


class TestPrintEquation(unittest.TestCase):

    def test_casos(self):
        A = [[-2.0, 1.0], [1e-13, 1.0], [0.0, 0.0], [0.5, -1.0], [-1.0, -0.5], [0.0, 3.0]]
        b = [1.0, 2.0, 1.0, -3.0, 0.0, 1 / 3]
        self.assertEqual(print_equation(A, b).splitlines(), [
            '-2x₁ + x₂ = 1',          # antes "2x₁ + x₂ = 1": se perdía el signo
            '1e-13x₁ + x₂ = 2',       # antes se ocultaba el 1e-13
            '0 = 1',                  # antes " = 1"
            '(1/2)x₁ - x₂ = -3',      # antes "1/2x₁ -x₂ = -3"
            '-x₁ - (1/2)x₂ = 0',
            '3x₂ = 1/3',
        ])

    def test_aproximaciones_entre_parentesis(self):
        self.assertEqual(print_equation([[1.9999999999999998, -1.0]], [0.0]), '(≈2)x₁ - x₂ = 0')

    def test_fila_nula_compatible(self):
        self.assertEqual(print_equation([[0.0, 0.0]], [0.0]), '0 = 0')


class TestCli(unittest.TestCase):

    def _correr(self, runner, entradas):
        it = iter(entradas)
        salida = io.StringIO()
        with mock.patch('builtins.input', lambda *a, **k: next(it)), redirect_stdout(salida):
            runner()
        return salida.getvalue()

    def test_gauss_y_gauss_jordan_con_entradas_1e_13(self):
        from cli.method_runners import run_gauss, run_gauss_jordan
        # 1e-13·[[2,1],[1,3]] x = 1e-13·(3,4) -> x = (1,1). El CLI no acepta
        # notación científica: se tipea en decimal.
        e = '0.0000000000001'
        entradas = ['2', '2', f'0.0000000000002 {e}', '0.0000000000003', f'{e} 0.0000000000003', '0.0000000000004']
        for runner in (run_gauss, run_gauss_jordan):
            with self.subTest(runner=runner.__name__):
                texto = self._correr(runner, entradas)
                self.assertIn('Status: unique', texto)
                self.assertIn('2e-13x₁ + 1e-13x₂ = 3e-13', texto)


class TestDeterminanteNoRepresentableEnGaussJordan(unittest.TestCase):

    def test_no_dice_det_cero_de_una_invertible(self):
        import warnings
        A = [[1e-110, 0.0, 0.0], [0.0, 1e-110, 0.0], [0.0, 0.0, 1e-110]]   # det = 1e-330
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)          # no se filtra el aviso
            g, r = resolver_gj(A, producto(A, [1, 2, 3]))
        self.assertEqual(r['status'], 'unique')
        textos = [st['text'] for st in g.frame if st['tag'] == 'det']
        self.assertEqual(len(textos), 1)
        self.assertIn('no representable', textos[0])
        self.assertNotIn('= 0', textos[0])
        self.assertTrue(residuo_ok(A, r['solution'], producto(A, [1, 2, 3])))


if __name__ == '__main__':
    unittest.main()
