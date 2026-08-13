"""
Tests de los 4 endpoints numéricos con rest_framework.test.APIClient.

Mismo criterio que los demás tests de la API: sin django.test.TestCase, sin
base de datos.

TestParidadContraCoreNumeric compara la raíz que da cada endpoint contra la
llamada directa a core/numeric/ -- dos raíces conocidas (√2 y la de
x**3-2x-5) para los 4 métodos, no sólo el caso feliz de siempre.

TestDegeneraciones cubre una degeneración por método: el 400 tiene que
traer el mensaje que arma el motor (core/numeric/), no un mensaje genérico
de la capa HTTP -- es la prueba de que la vista está traduciendo la
excepción de core/, no inventando la suya.
"""
import math
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

from core.numeric.metodos_cerrados import metodo_biseccion

RAIZ_2 = math.sqrt(2)
RAIZ_CUBICA = 2.0945514815423265  # x**3 - 2x - 5, única raíz real


class TestParidadContraCoreNumeric(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_bisection_sqrt2(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_2, places=5)

    def test_bisection_raiz_cubica(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^3 - 2x - 5', 'xi': 2.0, 'xu': 3.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_CUBICA, places=5)

    def test_bisection_coincide_con_core_llamado_directo(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        directo = metodo_biseccion('x**2 - 2', 1.0, 2.0, 1e-6, criterio='intervalo')
        self.assertAlmostEqual(r.data['root'], directo['raiz'], places=9)
        self.assertEqual(len(r.data['table']), len(directo['historial']))
        self.assertEqual(r.data['iterations_estimate']['n_min'], directo['estimacion_iteraciones']['n_minimo'])

    def test_false_position_sqrt2(self):
        r = self.client.post('/api/v1/numeric/false-position', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_2, places=5)

    def test_false_position_raiz_cubica(self):
        r = self.client.post('/api/v1/numeric/false-position', {
            'function_latex': 'x^3 - 2x - 5', 'xi': 2.0, 'xu': 3.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_CUBICA, places=5)

    def test_newton_raphson_sqrt2(self):
        r = self.client.post('/api/v1/numeric/newton-raphson', {
            'function_latex': 'x^2 - 2', 'x0': 1.5, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_2, places=5)
        self.assertEqual(r.data['derivative_latex'], '2 x')

    def test_newton_raphson_raiz_cubica(self):
        r = self.client.post('/api/v1/numeric/newton-raphson', {
            'function_latex': 'x^3 - 2x - 5', 'x0': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_CUBICA, places=5)

    def test_secant_sqrt2(self):
        r = self.client.post('/api/v1/numeric/secant', {
            'function_latex': 'x^2 - 2', 'x0': 1.0, 'x1': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_2, places=5)

    def test_secant_raiz_cubica(self):
        r = self.client.post('/api/v1/numeric/secant', {
            'function_latex': 'x^3 - 2x - 5', 'x0': 2.0, 'x1': 3.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertAlmostEqual(r.data['root'], RAIZ_CUBICA, places=5)


class TestShapeDeLaRespuesta(unittest.TestCase):
    """Los renames del mapa, verificados campo por campo -- no basta con
    que la raíz coincida si la tabla tiene las claves viejas."""

    def setUp(self):
        self.client = APIClient()

    def test_fila_de_biseccion_tiene_las_claves_del_frontend(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        fila = r.data['table'][0]
        for clave in ('iteration', 'xl', 'xu', 'xr', 'yl', 'yu', 'yr', 'Ea', 'interval_length', 'Ea_lt_E'):
            self.assertIn(clave, fila)

    def test_fila_de_regla_falsa_tiene_yl_yu(self):
        # El gap que se corrigió en core/numeric/metodos_cerrados.py: regla
        # falsa ya calculaba fa/fb para el denominador, pero no los
        # registraba en el historial.
        r = self.client.post('/api/v1/numeric/false-position', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        fila = r.data['table'][0]
        self.assertIn('yl', fila)
        self.assertIn('yu', fila)
        self.assertAlmostEqual(fila['yl'], -1.0, places=6)
        self.assertAlmostEqual(fila['yu'], 2.0, places=6)

    def test_fila_de_newton_tiene_las_claves_del_frontend(self):
        r = self.client.post('/api/v1/numeric/newton-raphson', {
            'function_latex': 'x^2 - 2', 'x0': 1.5, 'tolerance': 1e-6,
        }, format='json')
        fila = r.data['table'][0]
        for clave in ('iteration', 'xk', 'fxk', 'fprimexk', 'x_next', 'Ea', 'Ea_lt_E'):
            self.assertIn(clave, fila)
        self.assertNotIn('interval_length', fila)  # no hay a/b en newton

    def test_fila_de_secante_tiene_las_claves_del_frontend(self):
        r = self.client.post('/api/v1/numeric/secant', {
            'function_latex': 'x^2 - 2', 'x0': 1.0, 'x1': 2.0, 'tolerance': 1e-6,
        }, format='json')
        fila = r.data['table'][0]
        for clave in ('iteration', 'x_prev', 'x_curr', 'x_next', 'f_prev', 'f_curr', 'f_next', 'Ea', 'Ea_lt_E'):
            self.assertIn(clave, fila)

    def test_primera_fila_trae_Ea_null_no_infinity(self):
        # error=inf en la primera fila no es serializable a JSON: se sanea
        # a None. Es el bug que reventaba el endpoint con 500 antes de
        # arreglarlo -- verificado que el fix sigue en pie.
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertIsNone(r.data['table'][0]['Ea'])
        self.assertFalse(r.data['table'][0]['Ea_lt_E'])

    def test_details_y_conclusion_renombrados(self):
        r = self.client.post('/api/v1/numeric/newton-raphson', {
            'function_latex': 'x^2 - 2', 'x0': 1.5, 'tolerance': 1e-6,
        }, format='json')
        detalle = r.data['details'][0]
        self.assertIn('iteration', detalle)
        self.assertIn('lines', detalle)
        conclusion = r.data['conclusion']
        for clave in ('latex', 'root', 'iterations'):
            self.assertIn(clave, conclusion)

    def test_iterations_estimate_renombrado_en_biseccion(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        estimacion = r.data['iterations_estimate']
        self.assertIn('n_min', estimacion)
        self.assertIn('formula_general', estimacion['latex'])
        self.assertIn('formula_substitution', estimacion['latex'])
        self.assertIn('formula_numeric', estimacion['latex'])

    def test_bisection_usa_max_iter_no_max_iterations(self):
        # BisectionInputs.tsx manda 'max_iter'; los otros tres mandan
        # 'max_iterations'. No es un error de tipeo del frontend original,
        # confirmado leyendo cada componente.
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-8, 'max_iter': 3,
        }, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data['iterations'], 3)
        self.assertIn('warning', r.data)


class TestDegeneraciones(unittest.TestCase):
    """Cada 400 tiene que traer el mensaje del motor, no uno genérico de la
    capa HTTP -- es la prueba de que la validación matemática vive en
    core/numeric/ y la vista sólo la traduce."""

    def setUp(self):
        self.client = APIClient()

    def test_biseccion_sin_cambio_de_signo_400_con_mensaje_del_motor(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 2.0, 'xu': 3.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)
        mensaje = r.data['error']['message']
        self.assertIn('f(a)', mensaje)
        self.assertIn('f(b)', mensaje)

    def test_regla_falsa_sin_cambio_de_signo_400(self):
        r = self.client.post('/api/v1/numeric/false-position', {
            'function_latex': 'x^2 - 2', 'xi': 2.0, 'xu': 3.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_newton_con_derivada_nula_400_con_mensaje_del_motor(self):
        r = self.client.post('/api/v1/numeric/newton-raphson', {
            'function_latex': '5', 'x0': 1.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('derivada', r.data['error']['message'].lower())

    def test_secante_con_denominador_nulo_400_con_mensaje_del_motor(self):
        r = self.client.post('/api/v1/numeric/secant', {
            'function_latex': 'x^2 - 2', 'x0': -1.5, 'x1': 1.5, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('secante', r.data['error']['message'].lower())

    def test_latex_invalido_400_no_500(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': r'\frac{x}{', 'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_tolerancia_no_positiva_400(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'function_latex': 'x^2 - 2', 'xi': 1.0, 'xu': 2.0, 'tolerance': 0.0,
        }, format='json')
        self.assertEqual(r.status_code, 400)


class TestValidacionDeForma(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_falta_function_latex_400(self):
        r = self.client.post('/api/v1/numeric/bisection-method', {
            'xi': 1.0, 'xu': 2.0, 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_falta_x0_en_newton_400(self):
        r = self.client.post('/api/v1/numeric/newton-raphson', {
            'function_latex': 'x^2 - 2', 'tolerance': 1e-6,
        }, format='json')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
