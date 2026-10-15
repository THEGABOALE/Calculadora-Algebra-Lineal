"""
Issue #9: error absoluto y relativo.

    Ea = |m - m~|          Er = |m - m~| / |m|   (m != 0)

El núcleo (core/numeric/errores.py) calcula con decimal.Decimal sobre el
texto tal como se escribió: 0.3 - 0.1 da exactamente 0.2, no el
0.19999999999999998 de float. `decimales` sólo controla la presentación.

Los valores esperados se calculan aparte con fractions.Fraction (aritmética
racional exacta, sin pasar por el motor) para no validar el cambio contra sí
mismo.
"""
import os
import sys
import unittest
from decimal import Decimal
from fractions import Fraction

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

URL = '/api/v1/numeric/abs-rel-error'


def esperado(m, mt):
    """(Ea, Er) exactos con Fraction; Er es None si m = 0."""
    m, mt = Fraction(m), Fraction(mt)
    ea = abs(m - mt)
    return ea, (None if m == 0 else ea / abs(m))


class TestNucleo(unittest.TestCase):

    def setUp(self):
        from core.numeric.errores import calcular_error_absoluto_relativo, leer_decimal
        self.calcular = calcular_error_absoluto_relativo
        self.leer = leer_decimal

    def assertExacto(self, m, mt):
        r = self.calcular(m, mt)
        ea, er = esperado(m, mt)
        self.assertEqual(Fraction(r['error_absoluto']['valor']), ea)
        if er is None:
            self.assertIsNone(r['error_relativo']['valor'])
        else:
            # Er es un cociente: exacto hasta la precisión interna (50 cifras).
            self.assertLess(abs(Fraction(r['error_relativo']['valor']) - er), er * Fraction(1, 10 ** 45) + Fraction(1, 10 ** 300))
        return r

    def test_casos_con_signos_y_cero(self):
        for m, mt in [
            ('3.1415', '3.14'), ('3.14', '3.1415'),     # aproximación por debajo y por arriba
            ('-2', '-1.5'), ('-2', '2'), ('2', '-2'),   # negativos: nunca errores negativos
            ('5', '0'), ('7.25', '7.25'), ('0', '0.1'), ('0', '0'),
            ('1e-5', '1.1e-5'), ('123456789.987654321', '123456789.98765432'),
        ]:
            with self.subTest(m=m, mt=mt):
                r = self.assertExacto(m, mt)
                self.assertGreaterEqual(r['error_absoluto']['valor'], 0)
                if r['error_relativo']['valor'] is not None:
                    self.assertGreaterEqual(r['error_relativo']['valor'], 0)

    def test_sin_error_de_representacion_de_float(self):
        r = self.calcular('0.3', '0.1')
        self.assertEqual(r['error_absoluto']['valor'], Decimal('0.2'))
        self.assertNotEqual(0.3 - 0.1, 0.2)  # lo que daría float

    def test_iguales_dan_cero(self):
        r = self.calcular('7.25', '7.25', decimales=3)
        self.assertEqual(r['error_absoluto']['valor'], 0)
        self.assertEqual(r['error_relativo']['valor'], 0)
        self.assertEqual(r['error_absoluto']['texto'], '0.000')
        self.assertEqual(r['error_relativo']['texto'], '0.000')

    def test_m_cero_relativo_indefinido(self):
        r = self.calcular('0', '0.1')
        self.assertEqual(r['error_absoluto']['valor'], Decimal('0.1'))
        self.assertIsNone(r['error_relativo']['valor'])
        self.assertIsNone(r['error_relativo']['texto'])
        self.assertIn('indefinido', r['error_relativo']['nota'].lower())

    def test_decimales_solo_cambian_la_presentacion(self):
        a = self.calcular('3.1415', '3.14', decimales=2)
        b = self.calcular('3.1415', '3.14', decimales=10)
        self.assertEqual(a['error_absoluto']['valor'], b['error_absoluto']['valor'])
        self.assertEqual(a['error_relativo']['valor'], b['error_relativo']['valor'])
        self.assertEqual(b['error_absoluto']['texto'], '0.0015000000')
        # Con 2 decimales 0.0015 se vería como 0.00: se pasa a notación
        # científica para no mostrar como cero un error que no lo es.
        self.assertEqual(a['error_absoluto']['texto'], '1.50E-3')

    def test_redondeo_marcado_con_aprox(self):
        r = self.calcular('3.1415', '3.14', decimales=4)
        self.assertEqual(r['error_absoluto']['texto'], '0.0015')          # exacto
        self.assertEqual(r['error_relativo']['texto'], '≈ 0.0005')        # 0.000477...
        self.assertEqual(r['error_relativo']['porcentaje'], '≈ 0.0477 %')

    def test_valor_chico_no_se_muestra_como_cero(self):
        r = self.calcular('1e-9', '2e-9', decimales=6)
        self.assertNotIn('0.000000', r['error_absoluto']['texto'])
        self.assertEqual(r['error_absoluto']['texto'], '1.000000E-9')

    def test_formulas_y_sustitucion_con_negativos(self):
        r = self.calcular('-2', '-1.5')
        self.assertEqual(r['error_absoluto']['formula'], '|m - m̃|')
        self.assertEqual(r['error_absoluto']['sustitucion'], '|-2 - (-1.5)|')
        self.assertEqual(r['error_relativo']['formula'], ('|m - m̃|', '|m|'))
        self.assertEqual(r['error_relativo']['sustitucion'], ('|-2 - (-1.5)|', '|-2|'))

    def test_entradas_invalidas(self):
        for texto in ['', '   ', 'abc', 'nan', 'NaN', 'sNaN', 'inf', '-Infinity',
                      '1/3', '1,5', '1e1000', '1e-1000', '1' * 60]:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    self.leer(texto, 'm')

    def test_entradas_validas(self):
        self.assertEqual(self.leer(' 3.14 ', 'm'), Decimal('3.14'))
        self.assertEqual(self.leer('-2.5E-3', 'm'), Decimal('-0.0025'))
        self.assertEqual(self.leer('+7', 'm'), Decimal('7'))
        self.assertEqual(self.leer('.5', 'm'), Decimal('0.5'))

    def test_limites_de_magnitud_exactos(self):
        # Revisión de Codex (PR #28): adjusted() dejaba pasar 9e100 aunque
        # el límite documentado es 1e100.
        for texto in ['1e100', '-1e100', '1e-100', '-1e-100', '0', '0e500']:
            with self.subTest(texto=texto):
                self.leer(texto, 'm')
        for texto in ['9e100', '1.0000001e100', '-2e100', '9e-101', '-9.9e-101']:
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    self.leer(texto, 'm')

    def test_notacion_cientifica_redondea_mitad_hacia_arriba(self):
        # Revisión de Codex (PR #28): la rama científica usaba el contexto
        # decimal global (ROUND_HALF_EVEN) en vez de ROUND_HALF_UP.
        from core.numeric.errores import texto_redondeado
        self.assertEqual(texto_redondeado(Decimal('2.5e-7'), 0), '≈ 3E-7')
        self.assertEqual(texto_redondeado(Decimal('3.5e-7'), 0), '≈ 4E-7')
        self.assertEqual(texto_redondeado(Decimal('1.25e-9'), 1), '≈ 1.3E-9')
        self.assertEqual(texto_redondeado(Decimal('-2.5e-7'), 0), '≈ -3E-7')
        # La mantisa que redondea a 10 se renormaliza.
        self.assertEqual(texto_redondeado(Decimal('9.96e-7'), 1), '≈ 1.0E-6')
        self.assertEqual(texto_redondeado(Decimal('1e-9'), 6), '1.000000E-9')

    def test_presentacion_no_depende_del_contexto_global(self):
        from decimal import ROUND_DOWN, localcontext
        from core.numeric.errores import texto_redondeado
        with localcontext() as ctx:
            ctx.rounding = ROUND_DOWN
            ctx.prec = 3
            self.assertEqual(texto_redondeado(Decimal('2.9e-7'), 0), '≈ 3E-7')
            self.assertEqual(texto_redondeado(Decimal('0.123456789'), 6), '≈ 0.123457')
            r = self.calcular('3.1415', '3.14', decimales=4)
        self.assertEqual(r['error_relativo']['texto'], '≈ 0.0005')
        self.assertEqual(r['error_absoluto']['valor'], Decimal('0.0015'))

    def test_decimales_fuera_de_rango(self):
        for d in (-1, 16):
            with self.assertRaises(ValueError):
                self.calcular('1', '2', decimales=d)


class TestEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = APIClient(raise_request_exception=False)

    def post(self, payload, status=200):
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, status, getattr(r, 'data', None))
        return r.data

    def test_contrato_del_frontend(self):
        data = self.post({'true_value': '3.1415', 'approx_value': '3.14', 'decimals_display': 4})
        self.assertEqual(data['input']['true_value_pretty'], '3.1415')
        self.assertEqual(data['input']['approx_value_pretty'], '3.14')
        self.assertEqual(data['absolute_error']['operation'], {'numerator': '|m - m̃|'})
        self.assertEqual(data['absolute_error']['formula'], {'numerator': '|3.1415 - 3.14|'})
        self.assertEqual(data['absolute_error']['result'], '0.0015')
        self.assertEqual(data['relative_error']['operation'], {'numerator': '|m - m̃|', 'denominator': '|m|'})
        self.assertEqual(data['relative_error']['formula'], {'numerator': '|3.1415 - 3.14|', 'denominator': '|3.1415|'})
        self.assertEqual(data['relative_error']['result'], '≈ 0.0005')
        # Campos agregados (el frontend no depende de ellos).
        self.assertEqual(data['absolute_error']['exact'], '0.0015')
        self.assertEqual(data['relative_error']['percent'], '≈ 0.0477 %')
        self.assertTrue(data['relative_error']['defined'])
        self.assertEqual(data['input']['decimals_display'], 4)

    def test_valores_exactos_contra_fraction(self):
        for m, mt in [('-2', '2'), ('1e-5', '1.1e-5'), ('0.3', '0.1'), ('5', '0')]:
            with self.subTest(m=m, mt=mt):
                data = self.post({'true_value': m, 'approx_value': mt})
                ea, er = esperado(m, mt)
                self.assertEqual(Fraction(data['absolute_error']['exact']), ea)
                self.assertLess(abs(Fraction(data['relative_error']['exact']) - er), er * Fraction(1, 10 ** 45) + Fraction(1, 10 ** 300))

    def test_decimales_por_defecto_6(self):
        data = self.post({'true_value': '-2', 'approx_value': '-1.5'})
        self.assertEqual(data['absolute_error']['result'], '0.500000')
        self.assertEqual(data['relative_error']['result'], '0.250000')
        self.assertEqual(data['input']['decimals_display'], 6)

    def test_m_cero_relativo_null_con_explicacion(self):
        data = self.post({'true_value': '0', 'approx_value': '0.1'})
        self.assertEqual(data['absolute_error']['result'], '0.100000')
        self.assertIsNone(data['relative_error']['result'])
        self.assertIsNone(data['relative_error']['exact'])
        self.assertIsNone(data['relative_error']['percent'])
        self.assertFalse(data['relative_error']['defined'])
        self.assertIn('indefinido', data['relative_error']['note'].lower())

    def test_acepta_numeros_json(self):
        data = self.post({'true_value': 2, 'approx_value': 1.5})
        self.assertEqual(data['absolute_error']['exact'], '0.5')

    def assertValidacion(self, payload, campo):
        data = self.post(payload, status=400)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn(campo, data['error']['message'])
        mensaje = ' '.join(str(m) for m in data['error']['message'][campo])
        self.assertTrue(mensaje.strip())
        return mensaje

    def test_entradas_invalidas_400(self):
        for valor in ['', 'abc', 'NaN', 'inf', '-Infinity', '1/3', '1e1000', '9e100']:
            with self.subTest(valor=valor):
                self.assertValidacion({'true_value': valor, 'approx_value': '1'}, 'true_value')
                self.assertValidacion({'true_value': '1', 'approx_value': valor}, 'approx_value')

    def test_campos_faltantes_400(self):
        self.assertValidacion({'approx_value': '1'}, 'true_value')
        self.assertValidacion({'true_value': '1'}, 'approx_value')

    def test_mensajes_en_castellano(self):
        self.assertIn('valor verdadero', self.assertValidacion({'true_value': '', 'approx_value': '1'}, 'true_value').lower())
        self.assertIn('número', self.assertValidacion({'true_value': 'abc', 'approx_value': '1'}, 'true_value').lower())

    def test_decimals_display_invalido_400(self):
        for d in (-1, 16, 'x', 2.5):
            with self.subTest(d=d):
                self.assertValidacion({'true_value': '1', 'approx_value': '2', 'decimals_display': d}, 'decimals_display')

    def test_decimals_display_limites_validos(self):
        self.assertEqual(self.post({'true_value': '2', 'approx_value': '1', 'decimals_display': 0})['absolute_error']['result'], '1')
        self.assertEqual(self.post({'true_value': '2', 'approx_value': '1', 'decimals_display': 15})['absolute_error']['result'], '1.' + '0' * 15)


if __name__ == '__main__':
    unittest.main()
