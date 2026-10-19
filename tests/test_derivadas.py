"""
Issue #10: derivadas simbólicas, POST /api/v1/calculus/derivate.

Los resultados se validan por EQUIVALENCIA MATEMÁTICA, no por texto: la
expresión devuelta y la esperada (escrita a mano en este archivo) tienen que
diferir en 0 tras simplificar. Por separado se comprueba que el LaTeX
devuelto vuelve a parsearse (con el mismo traductor LaTeX de la API) a una
expresión equivalente: es LaTeX válido, no sólo texto que se le parece.
"""
import os
import subprocess
import sys
import unittest

_RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LAC_DIR = os.path.join(_RAIZ_REPO, 'linear_algebra_calculator')
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
from sympy import (E, Abs, Symbol, cos, exp, log, sign, simplify, sin, sqrt,
                   sympify)

URL = '/api/v1/calculus/derivate'
x = Symbol('x', real=True)
t = Symbol('t', real=True)


def a_sympy(texto, var):
    """Texto de sympy (str de la derivada) -> Expr con la variable real."""
    # "e" es la constante de Euler, como en core/numeric/_expresiones.py.
    return sympify(texto, locals={var.name: var, 'E': E, 'e': E})


def equivalentes(a, b):
    return simplify(a - b) == 0


class _Base(unittest.TestCase):
    def setUp(self):
        self.client = APIClient(raise_request_exception=False)

    def derivar(self, latex, variable=None, status=200):
        payload = {'function_latex': latex}
        if variable is not None:
            payload['variable'] = variable
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, status, getattr(r, 'data', None))
        return r.data

    def assertDerivada(self, latex, esperada, var=x, verificar_latex=True):
        data = self.derivar(latex, None if var is x else var.name)
        self.assertTrue(data['ok'])
        resultado = data['data']['result']
        obtenida = a_sympy(resultado['expression'], var)
        self.assertTrue(equivalentes(obtenida, esperada),
                        f"d/d{var}({latex}) = {obtenida}, se esperaba {esperada}")
        if not verificar_latex:
            return data
        # El LaTeX devuelto es válido y dice lo mismo.
        from api.adapters.latex import latex_a_texto
        desde_latex = a_sympy(latex_a_texto(resultado['latex']), var)
        self.assertTrue(equivalentes(desde_latex, esperada),
                        f"el LaTeX {resultado['latex']!r} no equivale a {esperada}")
        return data


class TestDerivadas(_Base):

    def test_polinomio(self):
        self.assertDerivada(r'x^{2}', 2 * x)

    def test_constante_da_cero(self):
        data = self.assertDerivada(r'7', 0)
        self.assertEqual(data['data']['result']['latex'], '0')
        self.assertEqual(data['data']['result']['expression'], '0')

    def test_lineal(self):
        self.assertDerivada(r'3x+2', 3)

    def test_producto(self):
        data = self.assertDerivada(r'x^{2}\sin(x)', x ** 2 * cos(x) + 2 * x * sin(x))
        # Forma de libro (suma), no la factorización x(x cos x + 2 sin x).
        self.assertEqual(data['data']['result']['expression'], 'x**2*cos(x) + 2*x*sin(x)')

    def test_cociente(self):
        self.assertDerivada(r'\frac{1}{x}', -1 / x ** 2)

    def test_regla_de_la_cadena(self):
        self.assertDerivada(r'\sin(x^{2})', 2 * x * cos(x ** 2))

    def test_exponencial(self):
        data = self.assertDerivada(r'e^{x}', exp(x))
        self.assertEqual(data['data']['result']['latex'], 'e^{x}')

    def test_logaritmo_natural(self):
        self.assertDerivada(r'\ln(x)', 1 / x)

    def test_combinadas_y_simplificadas(self):
        self.assertDerivada(r'e^{x}\sin(x)', exp(x) * (sin(x) + cos(x)))
        self.assertDerivada(r'\sqrt{x^{2}+1}', x / sqrt(x ** 2 + 1))
        self.assertDerivada(r'\ln(\cos(x))', -sin(x) / cos(x))
        # Simplificación que sí acorta: queda -2/(x-1)^2.
        data = self.assertDerivada(r'\frac{x+1}{x-1}', -2 / (x - 1) ** 2)
        self.assertNotIn('x + 1', data['data']['result']['expression'])
        # Identidad: la derivada es 0 exacto.
        self.assertDerivada(r'\sin^{2}(x)+\cos^{2}(x)', 0)

    def test_valor_absoluto_con_variable_real(self):
        # \operatorname{sign} no lo lee el parser LaTeX de sympy: se valida
        # la expresión, y que el LaTeX nombre la función signo.
        data = self.assertDerivada(r'\left|x\right|', sign(x), verificar_latex=False)
        self.assertIn('sign', data['data']['result']['latex'])

    def test_decimales_quedan_exactos(self):
        data = self.assertDerivada(r'0.5x^{2}+0.1x', x + sympify('1/10'))
        self.assertNotIn('.', data['data']['result']['expression'])

    def test_variable_distinta_de_x(self):
        data = self.assertDerivada(r't^{3}+\cos(t)', 3 * t ** 2 - sin(t), var=t)
        self.assertEqual(data['data']['input']['variable'], 't')

    def test_otra_letra_respecto_de_t_es_rechazada(self):
        data = self.derivar(r'x^{2}+t', 't', status=400)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('x', data['error']['message'])


class TestContrato(_Base):

    def test_forma_de_la_respuesta(self):
        data = self.derivar(r'x^{2}\sin(x)')
        self.assertIs(data['ok'], True)
        self.assertEqual(data['data']['input']['latex'], r'x^{2}\sin(x)')
        self.assertEqual(data['data']['input']['variable'], 'x')
        self.assertIsInstance(data['data']['result']['latex'], str)
        self.assertTrue(data['data']['result']['latex'])
        # Campos agregados: lo que se entendió de la entrada.
        self.assertEqual(data['data']['input']['expression'], 'x**2*sin(x)')
        self.assertEqual(data['data']['input']['interpreted_latex'], 'x^{2} \\sin{\\left(x \\right)}')

    def test_variable_por_defecto_x(self):
        self.assertEqual(self.derivar(r'x^{3}')['data']['input']['variable'], 'x')


class TestErrores(_Base):

    def assertError(self, latex, variable=None, fragmento=None):
        data = self.derivar(latex, variable, status=400)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertTrue(data['error']['message'])
        if fragmento:
            self.assertIn(fragmento, str(data['error']['message']).lower())
        return data

    def test_latex_vacio(self):
        self.assertError('', fragmento='function_latex')
        self.assertError('   ')

    def test_latex_invalido(self):
        self.assertError(r'\sin(')
        self.assertError(r'x^{')
        self.assertError(r'x+')
        self.assertError(r'x)')

    def test_funcion_desconocida_o_simbolos_ajenos(self):
        # \operatorname{sen} no es una función conocida: queda como letras
        # sueltas, que no son la variable.
        self.assertError(r'\operatorname{sen}(x)')
        self.assertError(r'x+y', fragmento='y')

    def test_operadores_de_calculo_rechazados(self):
        self.assertError(r'\int x dx', fragmento='integral')
        self.assertError(r'\frac{d}{dx}x^{2}', fragmento='derivada')

    def test_variable_invalida(self):
        for v in ('xy', 'e', '1', '', 'X', 'π'):
            with self.subTest(v=v):
                self.assertError('x^{2}', v, fragmento='variable')

    def test_falta_function_latex(self):
        r = self.client.post(URL, {}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data['error']['code'], 'VALIDATION_ERROR')

    def test_expresion_demasiado_larga(self):
        self.assertError('x+' * 300 + 'x', fragmento='larga')

    def test_nombres_peligrosos_no_se_ejecutan(self):
        for latex in (r'\operatorname{__import__}(x)', r'\operatorname{eval}(x)', r'\_\_import\_\_(x)'):
            with self.subTest(latex=latex):
                self.assertError(latex)


class TestNewtonConservaSuRegla(unittest.TestCase):
    """La derivada nula es un resultado válido para calculus/derivate, pero
    Newton-Raphson la sigue rechazando: f'(x) = 0 deja su fórmula sin
    definir."""

    def test_derivar_de_newton_rechaza_cero(self):
        from core.numeric._expresiones import derivar, parsear
        expr, var = parsear('7')
        with self.assertRaises(ValueError):
            derivar(expr, var)

    def test_newton_con_funcion_constante(self):
        from core.numeric.metodos_abiertos import metodo_newton_raphson
        with self.assertRaises(ValueError):
            metodo_newton_raphson('7', 1.0, 1e-6)

    def test_parsear_sigue_aceptando_solo_x_por_defecto(self):
        from core.numeric._expresiones import parsear
        with self.assertRaises(ValueError):
            parsear('t**2')


class TestImportsDiferidos(unittest.TestCase):

    def test_importar_core_calculo_no_carga_sympy(self):
        codigo = ("import sys; import core.calculo; "
                  "print('sympy' in sys.modules, 'antlr4' in sys.modules)")
        salida = subprocess.run(
            [sys.executable, '-c', codigo], capture_output=True, text=True,
            cwd=_RAIZ_REPO, env=dict(os.environ, PYTHONPATH=_LAC_DIR),
        )
        self.assertEqual(salida.returncode, 0, salida.stderr)
        self.assertEqual(salida.stdout.split(), ['False', 'False'])


if __name__ == '__main__':
    unittest.main()
