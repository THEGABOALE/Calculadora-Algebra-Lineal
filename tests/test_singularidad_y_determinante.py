"""
Singularidad registrada por Gauss-Jordan y determinante en escalas extremas.

1. GaussJordanMethod.run() registraba "Estado de singularidad" con
   self.is_singular() ANTES de eliminar; is_singular() lee el rango con
   analyze_argumented, que sólo vale para una matriz escalonada. Sin
   escalonar, cada fila no nula "tiene pivote": A = [[1,2],[2,4]] (rango 1)
   salía "no singular" justo debajo de "Determinante de A = 0".
2. GaussMethod.determinant_result() multiplicaba la diagonal con math.prod:
   diag(1e-200, 1e-200, 1e300) daba 0 (y el paso decía "no representable")
   aunque det = 1e-100. Mismo defecto en los productos de Sarrus
   (matrix/determinant method=sarrus daba 0.0 / inf) y en el det 3x3 de
   Cramer (rechazaba el sistema por "det no representable").

Los valores esperados son matemáticos (det de una diagonal = producto de la
diagonal; signo por permutación), no de otra función del motor.
"""
import copy
import math
import os
import random
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

A1 = [[1e-200, 0.0, 0.0], [0.0, 1e-200, 0.0], [0.0, 0.0, 1e300]]      # det = 1e-100
A2 = [[1e200, 0.0, 0.0], [0.0, 1e200, 0.0], [0.0, 0.0, 1e-300]]      # det = 1e100
A1_SWAP = [[0.0, 1e-200, 0.0], [1e-200, 0.0, 0.0], [0.0, 0.0, 1e300]]   # una transposición: det = -1e-100
A_UNDER = [[1e-110, 0.0, 0.0], [0.0, 1e-110, 0.0], [0.0, 0.0, 1e-110]]  # det = 1e-330: no representable
A_OVER = [[1e110, 0.0, 0.0], [0.0, 1e110, 0.0], [0.0, 0.0, 1e110]]     # det = 1e330: no representable


def gj(A, b):
    g = GaussJordanMethod(copy.deepcopy(A), list(b))
    antes = g.is_singular()
    g.run()
    return g, g.solve_and_log(), antes


def gauss(A, b):
    g = GaussMethod(copy.deepcopy(A), list(b))
    g.gauss_method()
    return g, g.solve_and_log()


def paso(frame, tag):
    pasos = [st for st in frame if st['tag'] == tag]
    return pasos[0]['text'] if len(pasos) == 1 else pasos


# ==========================================================================
# Hallazgo 1: singularidad en Gauss-Jordan
# ==========================================================================
class TestSingularidadRegistradaPorGaussJordan(unittest.TestCase):

    CASOS = [
        # (nombre, A, b, A singular, status, rango(A))
        ('filas proporcionales, compatible', [[1.0, 2.0], [2.0, 4.0]], [3.0, 6.0], True, 'infinite', 1),
        ('filas proporcionales, incompatible', [[1.0, 2.0], [2.0, 4.0]], [3.0, 7.0], True, 'inconsistent', 1),
        ('3x3 filas dependientes, compatible', [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], [6.0, 15.0, 24.0], True, 'infinite', 2),
        ('3x3 filas dependientes, incompatible', [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], [1.0, 1.0, 0.0], True, 'inconsistent', 2),
        ('matriz nula, compatible', [[0.0, 0.0], [0.0, 0.0]], [0.0, 0.0], True, 'infinite', 0),
        ('matriz nula, incompatible', [[0.0, 0.0], [0.0, 0.0]], [1.0, 0.0], True, 'inconsistent', 0),
        ('invertible', [[2.0, 1.0], [1.0, 3.0]], [3.0, 4.0], False, 'unique', 2),
        ('invertible con intercambio', [[0.0, 1.0], [1.0, 0.0]], [1.0, 1.0], False, 'unique', 2),
        ('invertible ~1e-13', [[2e-13, 1e-13], [1e-13, 3e-13]], [3e-13, 4e-13], False, 'unique', 2),
    ]

    def test_paso_inicial_resultado_y_metodo_coinciden(self):
        for nombre, A, b, singular, status, rango in self.CASOS:
            with self.subTest(caso=nombre):
                g, r, antes = gj(A, b)
                texto = paso(g.frame, 'singularity')
                if singular:
                    self.assertIn('de A: singular', texto)
                else:
                    self.assertIn('de A: no singular', texto)
                self.assertIs(antes, singular)               # antes de eliminar
                self.assertIs(r['is_singular'], singular)    # después de eliminar
                self.assertIs(g.is_singular(), singular)
                self.assertEqual(r['status'], status)
                self.assertEqual(r['rank'], rango)

    def test_el_frame_no_se_contradice(self):
        # det = 0 <=> singular <=> sin solución única, en los tres pasos.
        for nombre, A, b, singular, status, rango in self.CASOS:
            with self.subTest(caso=nombre):
                g, r, _ = gj(A, b)
                det_texto = paso(g.frame, 'det')
                self.assertEqual(det_texto == 'Determinante de A = 0', singular)
                self.assertEqual(r['status'] != 'unique', singular)
                resumen = paso(g.frame, 'summary')
                self.assertIn(f'Tipo de solución = {status}', resumen)

    def test_singular_no_es_incompatible(self):
        # El paso de singularidad no adelanta la compatibilidad.
        g, r, _ = gj([[1.0, 2.0], [2.0, 4.0]], [3.0, 6.0])
        texto = paso(g.frame, 'singularity')
        self.assertIn('se decide al eliminar', texto)
        self.assertNotIn('incompatible:', texto)
        self.assertEqual(r['status'], 'infinite')

    def test_rama_incompatible_trae_las_mismas_claves(self):
        _, r, _ = gj([[1.0, 2.0], [2.0, 4.0]], [3.0, 7.0])
        for clave in ('is_singular', 'determinant', 'tipo_sistema', 'dependencia', 'parametric_solution'):
            self.assertIn(clave, r)
        self.assertIs(r['is_singular'], True)
        self.assertEqual(r['determinant'], 0.0)

    def test_rectangular_no_aplica(self):
        g, r, antes = gj([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]], [1.0, 1.0, 1.0])
        self.assertIsNone(antes)
        self.assertIsNone(r['is_singular'])
        self.assertEqual(paso(g.frame, 'singularity'), [])

    def test_bateria_aleatoria_sin_contradicciones(self):
        random.seed(31)
        for _ in range(400):
            n = random.choice([2, 3])
            filas = [[float(random.randint(-4, 4)) for _ in range(n)] for _ in range(n)]
            if random.random() < 0.5:                       # forzar dependencia
                filas[-1] = [filas[0][j] * random.randint(-2, 2) for j in range(n)]
            b = [float(random.randint(-4, 4)) for _ in range(n)]
            g, r, antes = gj(filas, b)
            singular = mt.is_singular(filas)
            with self.subTest(A=filas, b=b):
                self.assertIs(antes, singular)
                self.assertIs(r['is_singular'], singular)
                self.assertEqual(r['status'] != 'unique', singular)
                self.assertEqual('de A: singular' in paso(g.frame, 'singularity'), singular)


class TestContratoApiGaussJordan(unittest.TestCase):

    def test_summary_de_reduce_mantiene_sus_claves(self):
        c = APIClient()
        for b in ([3.0, 6.0], [3.0, 7.0]):
            r = c.post('/api/v1/matrix/reduce', {'method': 'gauss-jordan', 'A': [[1.0, 2.0], [2.0, 4.0]], 'b': b}, format='json')
            self.assertEqual(r.status_code, 200, r.data)
            self.assertEqual(set(r.data['summary']), {'status', 'solution_type', 'solution', 'rank', 'ranks',
                                                      'basic_vars', 'free_vars', 'variables', 'inconsistent_rows'})
            textos = [st['operation'] for st in r.data['steps'] if st.get('tag') == 'singularity']
            self.assertEqual(len(textos), 1)
            self.assertIn('de A: singular', textos[0])


# ==========================================================================
# Hallazgo 2: determinante en escalas extremas
# ==========================================================================
class TestProductoSinDesborde(unittest.TestCase):

    def test_igual_al_producto_comun_sin_extremos(self):
        random.seed(32)
        for _ in range(3000):
            fs = [random.uniform(-10, 10) * 10 ** random.randint(-30, 30) for _ in range(random.randint(1, 5))]
            esperado = 1.0
            for f in fs:
                esperado *= f
            self.assertEqual(mt.producto_sin_desborde(fs), esperado)

    def test_extremos(self):
        self.assertTrue(math.isclose(mt.producto_sin_desborde([1e-200, 1e-200, 1e300]), 1e-100, rel_tol=1e-15))
        self.assertTrue(math.isclose(mt.producto_sin_desborde([1e200, 1e200, 1e-300]), 1e100, rel_tol=1e-15))
        self.assertTrue(math.isclose(mt.producto_sin_desborde([1e-200, 1e-200, 1e300], -1.0), -1e-100, rel_tol=1e-15))
        self.assertEqual(mt.producto_sin_desborde([1e-200, 0.0, 1e300]), 0.0)
        self.assertEqual(mt.producto_sin_desborde([1e-110] * 3), 0.0)          # 1e-330: subdesborda de verdad
        self.assertEqual(mt.producto_sin_desborde([1e110] * 3), math.inf)      # 1e330: desborda de verdad
        self.assertEqual(mt.producto_sin_desborde([1e110] * 3, -1.0), -math.inf)
        self.assertEqual(mt.producto_sin_desborde([]), 1.0)


class TestDeterminanteDeGauss(unittest.TestCase):

    def _det(self, A):
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            g, _ = gauss(A, [1.0, 1.0, 1.0])
        return g, g.determinante, paso(g.frame, 'det')

    def test_A1_y_A2(self):
        for A, esperado in ((A1, 1e-100), (A2, 1e100)):
            with self.subTest(esperado=esperado):
                g, det, texto = self._det(A)
                self.assertTrue(math.isclose(det, esperado, rel_tol=1e-12), det)
                self.assertNotIn('no representable', texto)
                self.assertIn(f'= {esperado:g}'.replace('e+', 'e'), texto)

    def test_intercambio_de_filas_cambia_el_signo(self):
        g, det, texto = self._det(A1_SWAP)
        self.assertTrue(math.isclose(det, -1e-100, rel_tol=1e-12), det)
        self.assertTrue(texto.startswith('Determinante de A = −('), texto)   # signo de la permutación
        swaps = [st['text'] for st in g.frame if st['tag'] == 'swap_rows']
        self.assertEqual(len(swaps), 1)
        self.assertIn('cambia el signo de det(A)', swaps[0])
        g2, det2, _ = self._det([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        self.assertEqual(det2, -1.0)

    def test_singular(self):
        g, det, texto = self._det([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
        self.assertEqual(det, 0.0)
        self.assertNotIn('no representable', texto)

    def test_genuinamente_fuera_de_rango(self):
        for A, esperado, palabra in ((A_UNDER, 0.0, 'subdesborda'), (A_OVER, math.inf, 'desborda')):
            with self.subTest(esperado=esperado):
                g, det, texto = self._det(A)
                self.assertEqual(det, esperado)
                self.assertIn('no representable', texto)
                self.assertIn(palabra, texto)
                self.assertIs(mt.is_singular(A), False)


class TestMismoDeterminanteEnTodasLasRutas(unittest.TestCase):
    """Gauss, Gauss-Jordan, matrix_tools, Cramer y matrix/determinant
    (sarrus, cofactores) no pueden mostrar determinantes contradictorios."""

    CASOS = [(A1, 1e-100), (A2, 1e100), (A1_SWAP, -1e-100),
             # cofactores pasa por el menor 1e-200·1e-200 = 1e-400
             ([[1e300, 0.0, 0.0], [0.0, 1e-200, 0.0], [0.0, 0.0, 1e-200]], 1e-100),
             ([[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], -1.0),
             ([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], 0.0)]

    def test_todas_coinciden(self):
        client = APIClient()
        for A, esperado in self.CASOS:
            with self.subTest(esperado=esperado):
                b = [sum(fila) for fila in A]          # b = A·(1,1,1): Cramer aplicable si det ≠ 0
                valores = {}
                g, _ = gauss(A, b)
                valores['gauss'] = g.determinante
                j, _, _ = gj(A, b)
                valores['gauss-jordan'] = j.determinante
                valores['matrix_tools'] = mt.determinant(A)
                valores['cramer'] = CramerMethod(copy.deepcopy(A), list(b)).solve()['determinant']
                for metodo in ('sarrus', 'cofactors'):
                    r = client.post('/api/v1/matrix/determinant', {'method': metodo, 'A': A}, format='json')
                    self.assertEqual(r.status_code, 200, r.data)
                    valores[metodo] = r.data['result']['determinant']
                for nombre, v in valores.items():
                    with self.subTest(ruta=nombre):
                        if esperado == 0.0:
                            self.assertEqual(v, 0.0)
                        else:
                            self.assertTrue(math.isclose(v, esperado, rel_tol=1e-12), (nombre, v))

    def test_sarrus_muestra_cada_diagonal_sin_subdesbordar(self):
        c = CramerMethod(A1, [0.0, 0.0, 0.0])
        c.calculate_determinant_sarrus(A1)
        d1 = [st['text'] for st in c.frame if st['tag'] == 'sarrus_d1'][0]
        self.assertTrue(d1.endswith('= 1e-100'), d1)

    def test_cramer_resuelve_A1_y_A2(self):
        for A in (A1, A2):
            with self.subTest(A=A):
                b = [sum(fila) for fila in A]
                r = CramerMethod(copy.deepcopy(A), b).solve()
                self.assertEqual(r['status'], 'unique')
                for xi in r['solution']:
                    self.assertTrue(math.isclose(xi, 1.0, rel_tol=1e-12))


class TestPerdidaIntermediaVsNoRepresentable(unittest.TestCase):

    def test_cofactores_explica_la_perdida_intermedia(self):
        A = [[1e300, 0.0, 0.0], [0.0, 1e-200, 0.0], [0.0, 0.0, 1e-200]]
        c = CramerMethod(A, [0.0, 0.0, 0.0])
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            det = c.calculate_determinant_cofactors(A)
        self.assertTrue(math.isclose(det, 1e-100, rel_tol=1e-12))
        nota = [st['text'] for st in c.frame if st['tag'] == 'cofactor_overflow']
        self.assertEqual(len(nota), 1)
        self.assertIn('producto intermedio', nota[0])

    def test_4x4_cramer_y_gauss(self):
        A = [[1e300, 0.0, 0.0, 0.0], [0.0, 1e-200, 0.0, 0.0], [0.0, 0.0, 1e-200, 0.0], [0.0, 0.0, 0.0, 1.0]]
        b = [sum(f) for f in A]
        r = CramerMethod(copy.deepcopy(A), b).solve()
        self.assertEqual(r['status'], 'unique')
        self.assertTrue(math.isclose(r['determinant'], 1e-100, rel_tol=1e-12))
        for xi in r['solution']:
            self.assertTrue(math.isclose(xi, 1.0, rel_tol=1e-12))
        g, _ = gauss(A, b)
        self.assertTrue(math.isclose(g.determinante, 1e-100, rel_tol=1e-12))

    def test_genuino_se_informa_igual_en_el_endpoint(self):
        client = APIClient()
        for metodo in ('sarrus', 'cofactors'):
            with self.subTest(metodo=metodo):
                r = client.post('/api/v1/matrix/determinant', {'method': metodo, 'A': A_UNDER}, format='json')
                self.assertEqual(r.status_code, 200, r.data)
                self.assertEqual(r.data['result']['determinant'], 0.0)
                notas = [st['operation'] for st in r.data['steps']['frame']['states'] if 'overflow' in (st.get('tag') or '')]
                self.assertEqual(len(notas), 1)
                self.assertIn('no representable', notas[0])
                self.assertIn('invertible', notas[0])


class TestCli(unittest.TestCase):

    def test_gauss_jordan_cli_registra_singular(self):
        import io
        from contextlib import redirect_stdout
        from unittest import mock
        from cli.method_runners import run_gauss_jordan
        it = iter(['2', '2', '1 2', '3', '2 4', '6'])
        salida = io.StringIO()
        with mock.patch('builtins.input', lambda *a, **k: next(it)), redirect_stdout(salida):
            run_gauss_jordan()
        texto = salida.getvalue()
        self.assertIn('Estado de singularidad de A: singular', texto)
        self.assertNotIn('de A: no singular', texto)
        self.assertIn('Status: infinite', texto)


if __name__ == '__main__':
    unittest.main()
