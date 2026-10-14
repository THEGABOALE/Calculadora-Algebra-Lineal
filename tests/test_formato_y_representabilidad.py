"""
Tercera vuelta de tolerancias numéricas:

1. format_number no puede presentar como iguales dos floats distintos
   (1000000000.25 salía "1000000000"; -1000000000.75, "-1000000001") ni
   perder cifras representables (1000000000000001.0 salía "1e15").
2. Fracciones didácticas (1/1024, 1/2048, 1/4096) sin volver a mostrar
   aproximaciones como pi como si fueran fracciones exactas.
3. determinant() == 0.0 NO equivale a singular: con |det| fuera del rango
   del double, una matriz invertible da 0.0 (o inf). Singularidad numérica
   y pérdida de representabilidad son cosas distintas.

Política de format_number bajo prueba (ver documentation/CriterioNumerico.md,
sección 5): exacta (el valor guardado), simplificada (a <= 128 ulps de un
entero / fracción legible / decimal de <= 10 cifras, sólo si el valor
necesita 16-17 cifras) o aproximación visible ("≈" + 10 cifras).
"""
import io
import math
import os
import random
import sys
import unittest
import warnings
from contextlib import redirect_stdout
from fractions import Fraction
from unittest import mock

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_RAIZ, 'linear_algebra_calculator'))

from core import matrix_tools as mt
from core.cramer import CramerMethod
from utils.EquationFunctions import format_number

ULPS = 128


def valor_mostrado(texto):
    """Número que denota una salida de format_number sin '≈'."""
    if '/' in texto:
        return float(Fraction(texto))
    return float(texto)


def diag(*vals):
    n = len(vals)
    return [[vals[i] if i == j else 0.0 for j in range(n)] for i in range(n)]


class TestNoOcultaDiferencias(unittest.TestCase):
    """Hallazgo 1."""

    CASOS = [
        (1000000000.25, '1000000000.25'),
        (1000000000000001.0, '1000000000000001'),
        (-1000000000.75, '-1000000000.75'),        # antes "-1000000001": otro entero
        (-123456789.5, '-123456789.5'),
        (-2500000000.5, '-2500000000.5'),
        (987654321.125, '987654321.125'),
        (-0.75, '-3/4'),
        (123456.75, '493827/4'),                   # numerador <= 1e6: fracción exacta
        (2.0 ** 53, '9007199254740992'),
        (2.0 ** 53 + 2, '9007199254740994'),
        (1e20, '1e20'),
    ]

    def test_casos(self):
        for valor, esperado in self.CASOS:
            with self.subTest(valor=valor):
                self.assertEqual(format_number(valor), esperado)

    def test_valores_limpios_se_muestran_exactos(self):
        # repr con <= 15 cifras => la salida denota exactamente el valor.
        random.seed(11)
        for _ in range(5000):
            cifras = random.randint(1, 15)
            v = float(f"{random.uniform(-1, 1) * 10 ** random.randint(-12, 12):.{cifras}g}")
            if v == 0:
                continue
            with self.subTest(v=v):
                s = format_number(v)
                self.assertFalse(s.startswith('≈'), s)
                self.assertEqual(valor_mostrado(s), v)


class TestRuidoDeComaFlotante(unittest.TestCase):
    """Presentación simplificada: sólo ruido de <= 128 ulps."""

    def test_cerca_de_enteros(self):
        for v, esperado in [(1.9999999999999998, '2'), (2.0000000000000004, '2'),
                            (99999.99999999999, '100000'), (-6.999999999999999, '-7'),
                            (3 + 128 * math.ulp(3.0), '3')]:
            with self.subTest(v=v):
                self.assertEqual(format_number(v), esperado)

    def test_mas_alla_de_128_ulps_es_aproximacion_visible(self):
        v = 3 + 200 * math.ulp(3.0)
        self.assertEqual(format_number(v), '≈3')

    def test_cero_coma_uno_mas_cero_coma_dos(self):
        self.assertEqual(0.1 + 0.2, 0.30000000000000004)
        self.assertEqual(format_number(0.1 + 0.2), '3/10')
        self.assertEqual(format_number(0.1 + 0.7), '4/5')

    def test_ruido_alrededor_de_decimales_cortos(self):
        # det calculado de diag(1e-8, 1e-8) es 1.0000000000000001e-16
        self.assertEqual(format_number(1.0000000000000001e-16), '1e-16')
        self.assertEqual(format_number(1.0000000000000002e-15), '1e-15')

    def test_lo_que_se_muestra_sin_aproximar_esta_a_128_ulps(self):
        # Propiedad: si no hay "≈", lo mostrado está a <= 128 ulps del valor.
        # (Dos floats a más de 256 ulps nunca comparten salida sin "≈".)
        random.seed(12)
        for _ in range(20000):
            v = random.uniform(-1, 1) * 10 ** random.uniform(-15, 15)
            s = format_number(v)
            if s.startswith('≈'):
                continue
            with self.subTest(v=v, s=s):
                self.assertLessEqual(abs(valor_mostrado(s) - v), ULPS * math.ulp(v))


class TestFraccionesDidacticas(unittest.TestCase):
    """Hallazgo 2."""

    def test_potencias_de_dos(self):
        for v, esperado in [(1 / 1024, '1/1024'), (1 / 2048, '1/2048'), (1 / 4096, '1/4096'),
                            (3 / 4096, '3/4096'), (-5 / 2048, '-5/2048')]:
            with self.subTest(v=v):
                self.assertEqual(format_number(v), esperado)

    def test_fracciones_usuales(self):
        for v, esperado in [(0.5, '1/2'), (1 / 3, '1/3'), (2 / 3, '2/3'), (1 / 7, '1/7'),
                            (0.1, '1/10'), (-2.5, '-5/2'), (23 / 7, '23/7')]:
            with self.subTest(v=v):
                self.assertEqual(format_number(v), esperado)

    def test_solucion_de_sistema_con_denominador_grande(self):
        # det = 1994 (p90 de los sistemas enteros medidos): antes (tope 1000)
        # salía en decimal. Cramer da la solución exacta en float.
        A = [[9.0, 2.0, -7.0], [5.0, -8.0, 3.0], [-4.0, 6.0, 9.0]]
        r = CramerMethod(A, [1.0, 0.0, 0.0]).solve()
        det = round(r['determinant'])
        for xi in r['solution']:
            s = format_number(xi)
            self.assertIn('/', s)
            self.assertEqual(Fraction(s).limit_denominator(10 ** 6) * det % 1, 0)

    def test_constantes_no_se_vuelven_fracciones(self):
        for v in (math.pi, math.e, math.sqrt(2), math.sqrt(3), math.log(2), (1 + 5 ** 0.5) / 2,
                  math.pi ** 2, 1 / math.pi):
            with self.subTest(v=v):
                s = format_number(v)
                self.assertTrue(s.startswith('≈'), s)
                self.assertNotIn('/', s)

    def test_pi_y_raiz_de_dos(self):
        self.assertEqual(format_number(math.pi), '≈3.141592654')
        self.assertEqual(format_number(math.sqrt(2)), '≈1.414213562')

    def test_denominador_fuera_de_tope_es_aproximacion(self):
        self.assertEqual(format_number(1 / 12347), '≈8.099133393e-5')


class TestNumerosChicosSiguenDistintosDeCero(unittest.TestCase):

    def test_chicos(self):
        for v, esperado in [(1e-15, '1e-15'), (-1e-15, '-1e-15'), (2.5e-10, '2.5e-10'),
                            (1e-7, '1e-7'), (5e-324, '5e-324'), (0.0, '0'), (-0.0, '0')]:
            with self.subTest(v=v):
                self.assertEqual(format_number(v), esperado)

    def test_ningun_no_nulo_es_cero(self):
        for e in range(-320, 308, 3):
            v = 3.7 * 10.0 ** e
            if v == 0:
                continue
            with self.subTest(v=v):
                self.assertNotIn(format_number(v), ('0', '≈0'))


class TestDeterminanteYRepresentabilidad(unittest.TestCase):
    """Hallazgo 3."""

    def _sin_avisos(self, f, *args):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            resultado = f(*args)
        self.assertEqual([str(x.message) for x in w], [])
        return resultado

    def test_producto_parcial_ya_no_subdesborda(self):
        # det = 1e-100 es representable; multiplicando de a uno daba 0.0.
        A = diag(1e-200, 1e-200, 1e300)
        self.assertTrue(math.isclose(self._sin_avisos(mt.determinant, A), 1e-100, rel_tol=1e-12))
        B = diag(1e200, 1e200, 1e-300)
        self.assertTrue(math.isclose(self._sin_avisos(mt.determinant, B), 1e100, rel_tol=1e-12))

    def test_invertible_con_det_que_subdesborda(self):
        A = diag(1e-110, 1e-110, 1e-110)        # det = 1e-330 < 5e-324
        self.assertEqual(mt.rank_of(A), 3)
        self.assertIs(mt.is_singular(A), False)
        with self.assertWarns(RuntimeWarning) as ctx:
            d = mt.determinant(A)
        self.assertEqual(d, 0.0)
        self.assertIn('subdesbordamiento', str(ctx.warning))
        # inverse no la rechaza ni dice "det(A) = 0"
        Ainv, texto = mt.inverse(A, check_props=False)
        self.assertTrue(math.isclose(Ainv[0][0], 1e110, rel_tol=1e-12))
        self.assertIn('no representable en coma flotante', texto)
        self.assertNotIn('Determinante de A = 0', texto)

    def test_invertible_con_det_que_desborda(self):
        A = diag(1e110, 1e110, 1e110)           # det = 1e330 > 1.8e308
        self.assertIs(mt.is_singular(A), False)
        with self.assertWarns(RuntimeWarning) as ctx:
            d = mt.determinant(A)
        self.assertEqual(d, math.inf)
        self.assertIn('desbordamiento', str(ctx.warning))

    def test_singular_da_cero_sin_aviso(self):
        self.assertEqual(self._sin_avisos(mt.determinant, [[1.0, 2.0], [2.0, 4.0]]), 0.0)
        self.assertEqual(self._sin_avisos(mt.determinant, diag(0.0, 1e-110, 1e-110)), 0.0)

    def test_signo_con_intercambios(self):
        A = [[0.0, 1e-200, 0.0], [1e-200, 0.0, 0.0], [0.0, 0.0, 1e300]]   # det = -1e-100
        self.assertTrue(math.isclose(self._sin_avisos(mt.determinant, A), -1e-100, rel_tol=1e-12))

    def test_cramer_sigue_rechazando_det_no_representable(self):
        with self.assertRaises(ValueError):
            CramerMethod(diag(1e-110, 1e-110, 1e-110), [1.0, 1.0, 1.0]).solve()


class TestCli(unittest.TestCase):

    def _correr(self, funcion, entradas):
        it = iter(entradas)
        salida = io.StringIO()
        with mock.patch('builtins.input', lambda *a, **k: next(it, '0')), \
                mock.patch('cli.matrix_runners.mem_list', lambda: []), \
                redirect_stdout(salida):
            funcion()
        return salida.getvalue()

    def test_inversa_de_1e_5_I3_no_se_rechaza(self):
        # Antes: el CLI chequeaba |det| <= 1e-12 ANTES de llamar a inverse().
        from cli.matrix_runners import run_matrix_inverse
        texto = self._correr(run_matrix_inverse, ['3', '3', '0.00001 0 0', '0 0.00001 0', '0 0 0.00001'])
        self.assertNotIn('es singular', texto)
        self.assertIn('100000', texto)

    def test_inversa_singular_sigue_rechazandose(self):
        from cli.matrix_runners import run_matrix_inverse
        texto = self._correr(run_matrix_inverse, ['2', '2', '1 2', '2 4'])
        self.assertIn('es singular', texto)

    def test_comparacion_de_metodos_con_det_grande(self):
        # Antes: |det - det1| < 1e-10 absoluto marcaba "diferentes" dos
        # cálculos correctos de un det ~1e24 que difieren en el redondeo.
        from utils.printMethods import compare_determinant_methods
        A = [[1.1e8, 2.3e8, 3.7e8], [4.1e8, 5.3e8, 6.7e8], [7.1e8, 8.3e8, 9.9e8]]
        c = CramerMethod(A, [0.0, 0.0, 0.0])
        salida = io.StringIO()
        with redirect_stdout(salida):
            compare_determinant_methods(c, A)
        self.assertIn('mismo resultado', salida.getvalue())


class TestDocumentacionConsistente(unittest.TestCase):

    def _leer(self, ruta):
        with open(os.path.join(_RAIZ, ruta), encoding='utf-8') as f:
            return f.read()

    def test_no_se_afirma_det_cero_si_y_solo_si_singular(self):
        doc = self._leer('documentation/CriterioNumerico.md')
        self.assertNotIn('determinant(A) == 0.0   <=>', doc)
        self.assertIn('sólo de ida', doc)
        self.assertIn('subdesbordamiento', doc)
        self.assertNotIn('si y sólo si `A` es numéricamente singular', self._leer('documentation/Matrices.md'))

    def test_docstrings_avisan_el_subdesbordamiento(self):
        self.assertIn('subdesbordamiento', mt.determinant.__doc__)
        self.assertIn('subdesborda', mt.is_singular.__doc__)


if __name__ == '__main__':
    unittest.main()
