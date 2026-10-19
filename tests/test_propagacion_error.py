"""
Issue #11: propagación de error, POST /api/v1/numeric/propagation-error.

    f'(x0)                          derivada simbólica evaluada
    Δy_aprox = f'(x0)·Δx            aproximación lineal (diferencial)
    Δy_real  = f(x0 + Δx) - f(x0)   incremento exacto
    e_a      = |Δy_real - Δy_aprox|

En modo "deg", x0 y Δx están en grados y la función se transforma ANTES de
derivar: sin(x) pasa a sin(πx/180), así que f'(x) = (π/180)·cos(πx/180).

Los valores esperados se calculan aparte: con fractions.Fraction cuando son
racionales y con math (float, tolerancia relativa) cuando no, sin pasar por
el motor.
"""
import math
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

URL = '/api/v1/numeric/propagation-error'
G = math.pi / 180


def esperado(f, df, x0, dx):
    """(f'(x0), Δy_aprox, Δy_real, e_a) en float, calculados con math."""
    d = df(x0)
    aprox = d * dx
    real = f(x0 + dx) - f(x0)
    return d, aprox, real, abs(real - aprox)


class _Base(unittest.TestCase):
    def setUp(self):
        self.client = APIClient(raise_request_exception=False)

    def post(self, function_latex, x0, delta_x, angle_mode=None, status=200, **extra):
        payload = {'function_latex': function_latex, 'x0': x0, 'delta_x': delta_x, **extra}
        if angle_mode is not None:
            payload['angle_mode'] = angle_mode
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, status, getattr(r, 'data', None))
        return r.data

    def assertValores(self, data, esperados, rel=1e-12):
        v = data['values']
        for clave, e in zip(('derivative_at_x0', 'delta_y_approx', 'delta_y_real', 'absolute_error'), esperados):
            with self.subTest(clave=clave):
                obtenido = float(v[clave])
                self.assertTrue(math.isclose(obtenido, e, rel_tol=rel, abs_tol=1e-15),
                                f'{clave}: {obtenido} != {e}')


class TestNucleo(unittest.TestCase):

    def setUp(self):
        from core.numeric.propagacion import propagar_error
        self.propagar = propagar_error

    def test_polinomio_exacto(self):
        # f = x², x0 = 2, Δx = 0.1:  f'(2) = 4, Δy ≈ 0.4, Δy = 2.1² - 4 = 0.41, e = 0.01.
        r = self.propagar('x**2', '2', '0.1')
        self.assertEqual(Fraction(str(r['derivada_en_x0'])), 4)
        self.assertEqual(Fraction(str(r['delta_y_aprox'])), Fraction(4, 10))
        self.assertEqual(Fraction(str(r['delta_y_real'])), Fraction(41, 100))
        self.assertEqual(Fraction(str(r['error_absoluto'])), Fraction(1, 100))

    def test_grados_factor_pi_sobre_180(self):
        from sympy import Symbol, cos, pi, simplify
        r = self.propagar('sin(x)', '30', '1', modo_angular='deg')
        x = Symbol('x', real=True)
        self.assertEqual(simplify(r['derivada'] - pi / 180 * cos(pi * x / 180)), 0)

    def test_dx_cero_da_todo_cero(self):
        r = self.propagar('x**3 + sin(x)', '1.5', '0')
        self.assertEqual(r['delta_y_aprox'], 0)
        self.assertEqual(r['delta_y_real'], 0)
        self.assertEqual(r['error_absoluto'], 0)

    def test_modo_angular_invalido(self):
        with self.assertRaises(ValueError):
            self.propagar('sin(x)', '1', '0.1', modo_angular='grad')


class TestCasos(_Base):

    def test_polinomio(self):
        data = self.post(r'x^{2}', '2', '0.1')
        s = data['steps']
        self.assertEqual(s['approx_delta_y']['result'], '0.400000')
        self.assertEqual(s['exact_delta_y']['result'], '0.410000')
        self.assertEqual(s['absolute_error']['result'], '0.010000')
        self.assertEqual(data['values']['delta_y_real'], '0.41')
        self.assertEqual(data['values']['absolute_error'], '0.01')
        self.assertEqual(data['result']['absolute_error'], '0.010000')

    def test_seno_radianes(self):
        data = self.post(r'\sin(x)', '0', '0.1', 'rad')
        self.assertValores(data, esperado(math.sin, math.cos, 0, 0.1))
        self.assertEqual(data['input']['angle_mode'], 'rad')

    def test_seno_grados(self):
        data = self.post(r'\sin(x)', '30', '1', 'deg')
        self.assertValores(data, esperado(lambda t: math.sin(t * G), lambda t: G * math.cos(t * G), 30, 1))
        # f'(30°) = π√3/360 ≈ 0.0151149, no cos(30) ni cos(30°).
        self.assertAlmostEqual(float(data['values']['derivative_at_x0']), math.pi * math.sqrt(3) / 360, places=12)
        self.assertIn(r'\frac{\pi', data['steps']['derivative']['formula']['derivative'])
        self.assertEqual(data['input']['angle_mode'], 'deg')

    def test_coseno_y_tangente_grados(self):
        self.assertValores(self.post(r'\cos(x)', '60', '2', 'deg'),
                           esperado(lambda t: math.cos(t * G), lambda t: -G * math.sin(t * G), 60, 2))
        self.assertValores(self.post(r'\tan(x)', '45', '1', 'deg'),
                           esperado(lambda t: math.tan(t * G), lambda t: G / math.cos(t * G) ** 2, 45, 1))

    def test_mixta_grados_no_toca_el_polinomio(self):
        data = self.post(r'x^{2}+\sin(x)', '10', '0.5', 'deg')
        self.assertValores(data, esperado(lambda t: t * t + math.sin(t * G),
                                          lambda t: 2 * t + G * math.cos(t * G), 10, 0.5))

    def test_no_trigonometrica_igual_en_ambos_modos(self):
        rad = self.post(r'x^{3}-2x', '1.5', '0.2', 'rad')
        deg = self.post(r'x^{3}-2x', '1.5', '0.2', 'deg')
        self.assertEqual(rad['values'], deg['values'])
        self.assertEqual(rad['steps']['absolute_error']['result'], deg['steps']['absolute_error']['result'])

    def test_constante(self):
        data = self.post(r'7', '3', '0.5')
        self.assertEqual(data['values']['derivative_at_x0'], '0')
        self.assertEqual(data['values']['delta_y_approx'], '0')
        self.assertEqual(data['values']['delta_y_real'], '0')
        self.assertEqual(data['values']['absolute_error'], '0')

    def test_delta_x_cero(self):
        data = self.post(r'e^{x}\cos(x)', '1', '0')
        for clave in ('delta_y_approx', 'delta_y_real', 'absolute_error'):
            self.assertEqual(data['values'][clave], '0', clave)

    def test_fracciones_y_pi(self):
        # x0 = π/4, Δx = 1/100 en radianes.
        data = self.post(r'\sin(x)', r'\frac{\pi}{4}', r'\frac{1}{100}', 'rad')
        self.assertValores(data, esperado(math.sin, math.cos, math.pi / 4, 0.01))
        self.assertIn(r'\frac{\pi}{4}', data['input']['x0_latex'])
        # En grados, π es el número 3.14159…, no 180°.
        data = self.post(r'x^{2}', r'2\pi', r'\frac{1}{2}', 'deg')
        self.assertValores(data, esperado(lambda t: t * t, lambda t: 2 * t, 2 * math.pi, 0.5))

    def test_espacios_de_mathquill(self):
        # MathQuill puede emitir "\ " o "\," al escribir un espacio; no son
        # parte de la matemática y no deben romper el parser estricto.
        data = self.post(r'\sqrt{\ x}', r'\pi\ \frac{1}{4}', r'0.01', 'rad')
        self.assertValores(data, esperado(math.sqrt, lambda t: 1 / (2 * math.sqrt(t)), math.pi / 4, 0.01))
        data = self.post(r'2\,x^{2}', r'1', r'\frac{1}{2}')
        self.assertEqual(data['values']['delta_y_real'], '2.5')

    def test_decimales_negativos_y_e(self):
        self.assertValores(self.post(r'\ln(x)', 'e', '-0.25'),
                           esperado(math.log, lambda t: 1 / t, math.e, -0.25))

    def test_modo_omitido_es_radianes(self):
        omitido = self.post(r'\sin(x)', '1', '0.1')
        rad = self.post(r'\sin(x)', '1', '0.1', 'rad')
        self.assertEqual(omitido['values'], rad['values'])
        self.assertEqual(omitido['input']['angle_mode'], 'rad')

    def test_sin_redondeo_prematuro(self):
        # Error de orden 1e-9: con 6 decimales no puede mostrarse como 0.
        data = self.post(r'x^{2}', '1', '0.00003')
        self.assertEqual(Fraction(data['values']['absolute_error']), Fraction(9, 10 ** 10))
        self.assertNotEqual(data['steps']['absolute_error']['result'], '0.000000')

    def test_decimales_de_presentacion(self):
        data = self.post(r'x^{2}', '2', '0.1', decimals=2)
        self.assertEqual(data['steps']['exact_delta_y']['result'], '0.41')
        self.assertEqual(data['values']['delta_y_real'], '0.41')


class TestContrato(_Base):

    def test_claves_del_frontend(self):
        data = self.post(r'\sin(x)', '30', '1', 'deg')
        self.assertEqual(data['input']['function_latex'], r'\sin(x)')
        self.assertIsInstance(data['input']['x0'], str)
        self.assertIsInstance(data['input']['delta_x'], str)
        s = data['steps']
        for camino in (('derivative', 'formula', 'derivative'), ('derivative', 'formula', 'evaluation'),
                       ('approx_delta_y', 'formula', 'expression'), ('approx_delta_y', 'result'),
                       ('exact_delta_y', 'formula', 'expression'), ('exact_delta_y', 'result'),
                       ('absolute_error', 'formula', 'numerator'), ('absolute_error', 'result')):
            valor = s
            for clave in camino:
                valor = valor[clave]
            with self.subTest(camino=camino):
                self.assertIsInstance(valor, str)
                self.assertTrue(valor)

    def test_latex_de_los_pasos_es_valido(self):
        # Los pasos se renderizan con KaTeX: llaves balanceadas y sin
        # notación E cruda de Python.
        for args in ((r'x^{2}', '1', '0.00003'), (r'\sin(x)', '30', '1', 'deg'), (r'\ln(x)', 'e', '-0.25')):
            data = self.post(*args)
            for paso in data['steps'].values():
                for texto in paso['formula'].values():
                    self.assertEqual(texto.count('{'), texto.count('}'), texto)
                    self.assertNotRegex(texto, r'\dE[+-]?\d', texto)
                    # Sin caracteres de control (un "\a" o "\f" mal escapado).
                    self.assertNotRegex(texto, r'[\x00-\x08\x0b-\x1f]', repr(texto))
                    self.assertNotIn('≈', texto)  # en LaTeX va \approx

    def test_resultados_coherentes_con_los_pasos(self):
        data = self.post(r'x^{2}', '2', '0.1')
        s = data['steps']
        self.assertIn('0.41', s['exact_delta_y']['formula']['expression'])
        self.assertIn('4', s['derivative']['formula']['evaluation'])
        self.assertIn('0.4', s['approx_delta_y']['formula']['expression'])


class TestErrores(_Base):

    def assertValidacion(self, *args, fragmento=None, **kw):
        data = self.post(*args, status=400, **kw)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        mensaje = str(data['error']['message'])
        self.assertTrue(mensaje)
        if fragmento:
            self.assertIn(fragmento, mensaje.lower())
        return data

    def test_modo_angular_invalido(self):
        self.assertValidacion(r'\sin(x)', '1', '0.1', 'grados', fragmento='angle_mode')

    def test_entradas_vacias(self):
        self.assertValidacion('', '1', '0.1')
        self.assertValidacion(r'x^{2}', '', '0.1')
        self.assertValidacion(r'x^{2}', '1', '')

    def test_variables_donde_van_numeros(self):
        self.assertValidacion(r'x^{2}', 'x', '0.1', fragmento='x₀')
        self.assertValidacion(r'x^{2}', '1', 'y', fragmento='δx')

    def test_funcion_desconocida_o_letras_ajenas(self):
        self.assertValidacion(r'\operatorname{sen}(x)', '1', '0.1')
        self.assertValidacion(r'x+y', '1', '0.1')

    def test_latex_incompleto(self):
        self.assertValidacion(r'x^{', '1', '0.1')
        self.assertValidacion(r'x^{2}', r'\frac{1}{', '0.1')

    def test_fuera_del_dominio(self):
        self.assertValidacion(r'\frac{1}{x}', '0', '0.1', fragmento='dominio')
        self.assertValidacion(r'\ln(x)', '1', '-2', fragmento='dominio')     # ln(-1)
        self.assertValidacion(r'\sqrt{x}', '-1', '0.5', fragmento='dominio')  # valor complejo

    def test_derivada_no_definida_en_x0(self):
        self.assertValidacion(r'\sqrt{x}', '0', '0.25', fragmento='deriva')
        self.assertValidacion(r'\left|x\right|', '0', '0.1', fragmento='deriva')

    def test_valores_no_finitos_o_complejos(self):
        self.assertValidacion(r'x^{2}', r'\infty', '0.1')
        self.assertValidacion(r'x^{2}', r'\sqrt{-1}', '0.1')

    def test_trigonometricas_sin_conversion_en_grados(self):
        # Sólo sin, cos y tan se convierten a grados: sec, inversas, etc.
        # darían un resultado en radianes presentado como grados.
        self.assertValidacion(r'\sec(x)', '30', '1', 'deg', fragmento='grados')
        self.assertValidacion(r'\arcsin(x)', '0.5', '0.1', 'deg', fragmento='grados')
        # En radianes sí se admiten.
        self.post(r'\sec(x)', '0.5', '0.1', 'rad')

    def test_decimales_fuera_de_rango(self):
        self.assertValidacion(r'x^{2}', '1', '0.1', decimals=16, fragmento='decimals')


class TestOtrosEndpointsSinCambios(_Base):

    def test_secante_newton_y_derivadas(self):
        r = self.client.post('/api/v1/numeric/secant', {'function_latex': r'\sin(x)-0.5', 'x0': 20, 'x1': 40,
                                                        'tolerance': 1e-8, 'angle_mode': 'deg'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.data['root'], 30.0, places=7)
        r = self.client.post('/api/v1/numeric/newton-raphson', {'function_latex': '7', 'x0': 1, 'tolerance': 1e-6},
                             format='json')
        self.assertEqual(r.status_code, 400)  # Newton sigue rechazando f' = 0
        r = self.client.post('/api/v1/calculus/derivate', {'function_latex': r'\sin(x)'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('180', r.data['data']['result']['latex'])


if __name__ == '__main__':
    unittest.main()
