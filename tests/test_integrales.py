"""
Issue #12: integrales indefinidas, POST /api/v1/calculus/integral.

    ∫ f(x) dx = F(x) + C,   F'(x) = f(x)

Cada primitiva se verifica de forma independiente en este archivo: se
deriva F y se compara con el integrando en varios puntos reales donde el
integrando está definido (la comparación numérica cubre también las formas
con |·|, como ln|x|, donde simplify no siempre reduce la diferencia a 0).
El LaTeX devuelto se comprueba aparte: termina en "+ C" una sola vez y,
cuando no usa funciones especiales, vuelve a parsearse a la misma primitiva.
"""
import multiprocessing
import os
import sys
import time
import unittest
from unittest import mock

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
from sympy import E, Rational, Symbol, diff, nsimplify, sympify

URL = '/api/v1/calculus/integral'
PUNTOS = [Rational(n, 7) for n in (-23, -13, -6, -2, 3, 5, 11, 19, 30)]


def expr(texto, var):
    # Racionales exactos, como el motor (0.5 -> 1/2): un float de 15 cifras en
    # el integrando ensuciaría la comparación con la primitiva exacta.
    return nsimplify(sympify(texto, locals={var.name: var, 'E': E, 'e': E}), rational=True)


def assertPrimitiva(test, F, f, var):
    """F' = f en los puntos de PUNTOS donde f es real y finita."""
    dF = diff(F, var)
    comparados = 0
    for p in PUNTOS:
        fv = f.subs(var, p).evalf(30)
        if not (fv.is_real and fv.is_finite):
            continue
        dv = dF.subs(var, p).evalf(30)
        test.assertTrue(dv.is_real and dv.is_finite, f"F'({p}) = {dv}")
        test.assertLess(abs(dv - fv), 1e-20 * max(1, abs(fv)), f"F'({p}) = {dv} != f({p}) = {fv}")
        comparados += 1
    test.assertGreater(comparados, 0, 'ningún punto del dominio para comparar')


class TestNucleo(unittest.TestCase):
    """core/calculo.integrar_simbolica en el mismo proceso (sin límite de tiempo)."""

    def setUp(self):
        from core.calculo import integrar_simbolica
        self.integrar = integrar_simbolica

    def assertIntegral(self, f_texto, var='x', esperado=None):
        v = Symbol(var, real=True)
        r = self.integrar(f_texto, var)
        F = expr(r['primitiva_texto'], v)
        assertPrimitiva(self, F, expr(f_texto, v), v)
        if esperado is not None:
            self.assertEqual(r['primitiva_texto'], esperado)
        latex = r['primitiva_latex']
        self.assertTrue(latex == 'C' or latex.endswith(' + C'), latex)
        self.assertEqual(latex.count('+ C') + (latex == 'C'), 1, latex)
        self.assertNotIn('C', r['primitiva_texto'])
        return r

    def test_casos_basicos(self):
        self.assertIntegral('x**2', esperado='x**3/3')
        self.assertIntegral('7', esperado='7*x')
        self.assertIntegral('sin(x)', esperado='-cos(x)')
        self.assertIntegral('cos(x)', esperado='sin(x)')
        self.assertIntegral('e**x', esperado='exp(x)')
        self.assertIntegral('1/(x**2+1)', esperado='atan(x)')

    def test_cero_da_solo_c(self):
        r = self.assertIntegral('0', esperado='0')
        self.assertEqual(r['primitiva_latex'], 'C')

    def test_logaritmo_natural_conserva_su_dominio(self):
        # ∫ln x = x ln x − x: el integrando sólo existe para x > 0, no se
        # agrega |x|.
        r = self.assertIntegral('log(x)', esperado='x*log(x) - x')
        self.assertIn(r'\ln', r['primitiva_latex'])

    def test_uno_sobre_x_es_ln_valor_absoluto(self):
        # ∫1/x = ln|x|: válida en cada intervalo que no contiene al 0 (también
        # x < 0, donde ln x no existe).
        r = self.assertIntegral('1/x', esperado='log(Abs(x))')
        self.assertIn(r'\left|', r['primitiva_latex'])

    def test_logaritmos_de_argumento_positivo_sin_valor_absoluto(self):
        self.assertIntegral('2*x/(x**2+1)', esperado='log(x**2 + 1)')
        self.assertIntegral('tan(x)', esperado='-log(Abs(cos(x)))')

    def test_variable_t(self):
        self.assertIntegral('t**2', var='t', esperado='t**3/3')

    def test_decimales_a_racionales(self):
        r = self.assertIntegral('0.5*x**2 + 0.25')
        self.assertNotIn('.', r['primitiva_texto'])
        self.assertEqual(expr(r['primitiva_texto'], Symbol('x', real=True)),
                         expr('x**3/6 + x/4', Symbol('x', real=True)))

    def test_compuestas(self):
        self.assertIntegral('x*e**(x**2)')
        self.assertIntegral('cos(3*x)')
        self.assertIntegral('sqrt(1 - x**2)')
        self.assertIntegral('1/(x**2 - 1)')

    def test_funciones_especiales_admitidas_y_verificadas(self):
        for f, especial in [('e**(-x**2)', 'erf'), ('1/log(x)', 'li'), ('sin(x)/x', 'Si'),
                            ('e**x/x', 'Ei'), ('sin(x**2)', 'fresnels')]:
            with self.subTest(f=f):
                r = self.assertIntegral(f)
                self.assertIn(especial, r['funciones_especiales'])
                self.assertTrue(r['nota'])
                self.assertNotIn('gamma', r['primitiva_texto'])  # constantes simplificadas
                # MathQuill 0.10 no renderiza el espaciado \, (lo deja vacío).
                for definicion in r['definiciones'].values():
                    self.assertNotIn(r'\,', definicion)

    def test_sin_resolver_no_se_presenta_como_resuelta(self):
        from core.calculo import IntegralNoResuelta
        for f in ('x**x', 'sin(sin(x))', 'sqrt(tan(x))'):
            with self.subTest(f=f):
                with self.assertRaises(IntegralNoResuelta) as ctx:
                    self.integrar(f, 'x')
                mensaje = str(ctx.exception).lower()
                self.assertIn('no encontró', mensaje)
                # No afirma que no exista una primitiva elemental.
                self.assertNotIn('no tiene primitiva', mensaje)
                self.assertNotIn('no existe', mensaje)

    def test_resultado_por_tramos_no_admitido(self):
        from core.calculo import IntegralNoResuelta
        with self.assertRaises(IntegralNoResuelta):
            self.integrar('Abs(x)', 'x')

    def test_entradas_invalidas(self):
        for f, v in [('', 'x'), ('x**2', 'e'), ('x**2', 'xy'), ('x + t', 't'), ('y', 'x')]:
            with self.subTest(f=f, v=v):
                with self.assertRaises(ValueError):
                    self.integrar(f, v)

    def test_complejidad_maxima(self):
        f = ' + '.join(f'x**{k}*sin(x)' for k in range(1, 22))
        self.assertLess(len(f), 500)
        with self.assertRaises(ValueError) as ctx:
            self.integrar(f, 'x')
        self.assertIn('compleja', str(ctx.exception))


class TestLimiteDeTiempo(unittest.TestCase):
    """El cálculo corre en un proceso aparte que se mata al vencer el plazo."""

    def test_integral_costosa_se_corta(self):
        from core.calculo import CalculoDemasiadoCostoso, integrar_con_limite
        inicio = time.perf_counter()
        # 1/(x^5 + x + 1): sympy tarda más de 30 s.
        with self.assertRaises(CalculoDemasiadoCostoso):
            integrar_con_limite('1/(x**5 + x + 1)', 'x', segundos=3)
        self.assertLess(time.perf_counter() - inicio, 8)
        # El proceso se terminó: no queda nada consumiendo CPU.
        time.sleep(0.2)
        self.assertEqual(multiprocessing.active_children(), [])

    def test_caso_normal_dentro_del_plazo(self):
        from core.calculo import integrar_con_limite
        r = integrar_con_limite('x**2', 'x', segundos=20)
        self.assertEqual(r['primitiva_texto'], 'x**3/3')
        self.assertEqual(multiprocessing.active_children(), [])

    def test_errores_viajan_desde_el_proceso(self):
        from core.calculo import IntegralNoResuelta, integrar_con_limite
        with self.assertRaises(IntegralNoResuelta):
            integrar_con_limite('x**x', 'x', segundos=20)
        with self.assertRaises(ValueError):
            integrar_con_limite('y', 'x', segundos=20)


class TestEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = APIClient(raise_request_exception=False)

    def post(self, latex, variable=None, status=200):
        payload = {'function_latex': latex}
        if variable is not None:
            payload['variable'] = variable
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, status, getattr(r, 'data', None))
        return r.data

    def test_contrato(self):
        data = self.post(r'x^{2}', 'x')
        self.assertIs(data['ok'], True)
        self.assertEqual(data['data']['input'], {
            'latex': r'x^{2}', 'variable': 'x', 'interpreted_latex': 'x^{2}', 'expression': 'x**2',
        })
        self.assertEqual(data['data']['result']['latex'], r'\frac{x^{3}}{3} + C')
        self.assertEqual(data['data']['result']['expression'], 'x**3/3')
        self.assertEqual(data['data']['result']['special_functions'], [])
        self.assertIsNone(data['data']['result']['note'])

    def test_latex_valido_y_reparseable(self):
        from api.adapters.latex import latex_a_texto
        x = Symbol('x', real=True)
        for f_latex, f in [(r'\frac{1}{x}', '1/x'), (r'\ln(x)', 'log(x)'), (r'\frac{1}{x^{2}+1}', '1/(x**2+1)'),
                           (r'\sin(x)', 'sin(x)')]:
            with self.subTest(f=f_latex):
                latex = self.post(f_latex)['data']['result']['latex']
                self.assertTrue(latex.endswith(' + C'))
                F = expr(latex_a_texto(latex[:-len(' + C')], estricto=True), x)
                assertPrimitiva(self, F, expr(f, x), x)

    def test_variable_omitida_y_t(self):
        self.assertEqual(self.post(r'x^{2}')['data']['input']['variable'], 'x')
        data = self.post(r't^{2}', 't')
        self.assertEqual(data['data']['result']['expression'], 't**3/3')

    def test_funcion_especial(self):
        data = self.post(r'e^{-x^{2}}')
        self.assertEqual(data['data']['result']['special_functions'], ['erf'])
        self.assertIn('erf', data['data']['result']['latex'])
        self.assertTrue(data['data']['result']['note'])

    def test_errores_de_entrada_400(self):
        for latex, variable in [('', None), (r'x^{', None), (r'x^{2}', 'e'), (r'x+t', 't'),
                                (r'\int x dx', None), (r'2^{1000000000}x', None)]:
            with self.subTest(latex=latex, variable=variable):
                data = self.post(latex, variable, status=400)
                self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
                self.assertTrue(data['error']['message'])

    def test_sin_resolver_422(self):
        data = self.post(r'x^{x}', status=422)
        self.assertEqual(data['error']['code'], 'INTEGRAL_NOT_RESOLVED')
        self.assertIn('no encontró', data['error']['message'].lower())

    def test_sin_turno_503(self):
        import threading
        with mock.patch('core.calculo._EN_CURSO', threading.BoundedSemaphore(1)) as sem, \
                mock.patch('core.calculo._ESPERA_TURNO_S', 0.1):
            sem.acquire()  # otra integral "en curso" ocupa el único turno
            data = self.post(r'x^{2}', status=503)
        self.assertEqual(data['error']['code'], 'SERVER_BUSY')

    def test_tiempo_agotado_422(self):
        inicio = time.perf_counter()
        with mock.patch('core.calculo.TIEMPO_MAXIMO_INTEGRAL_S', 3):
            data = self.post(r'\frac{1}{x^{5}+x+1}', status=422)
        self.assertEqual(data['error']['code'], 'INTEGRAL_TIMEOUT')
        self.assertLess(time.perf_counter() - inicio, 8)


class TestRegresiones(unittest.TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_otros_endpoints(self):
        r = self.client.post('/api/v1/calculus/derivate', {'function_latex': r't^{3}', 'variable': 't'}, format='json')
        self.assertEqual(r.data['data']['result']['expression'], '3*t**2')
        r = self.client.post('/api/v1/calculus/derivate', {'function_latex': '7'}, format='json')
        self.assertEqual(r.data['data']['result']['latex'], '0')
        r = self.client.post('/api/v1/numeric/secant', {'function_latex': r'\sin(x)-0.5', 'x0': 20, 'x1': 40,
                                                        'tolerance': 1e-8, 'angle_mode': 'deg'}, format='json')
        self.assertAlmostEqual(r.data['root'], 30.0, places=7)
        r = self.client.post('/api/v1/numeric/propagation-error', {'function_latex': r'\sin(x)', 'x0': '30',
                                                                   'delta_x': '1', 'angle_mode': 'deg'}, format='json')
        self.assertIn('180', r.data['steps']['derivative']['formula']['derivative'])
        r = self.client.post('/api/v1/numeric/newton-raphson', {'function_latex': '7', 'x0': 1, 'tolerance': 1e-6},
                             format='json')
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
