"""
Regresión del issue #24: el método de la Secante ignoraba angle_mode.

La pantalla ofrece rad/deg y envía angle_mode, pero el serializer lo aceptaba
sin usarlo: con 'deg' la API respondía 200 con la raíz de la función en
radianes (sin(x) - 0.5 en [20, 40] -> 52.88 en vez de 30) y aceptaba
cualquier valor. Ahora:

- angle_mode sólo admite 'rad' o 'deg' (omitido = 'rad'); otro valor -> 400.
- con 'deg', los argumentos de sin/cos/tan se interpretan en grados
  (sin(x) se evalúa como sin(pi*x/180)); el resto de la expresión no cambia.
- con 'rad' (u omitido) el resultado es idéntico al de antes.

Las comprobaciones de residuo usan math directamente, independiente de
sympy y del motor, para no validar el cambio contra sí mismo.
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

from core.numeric.metodos_abiertos import metodo_secante

URL = '/api/v1/numeric/secant'
TOL = 1e-8


def sen_g(x):
    return math.sin(math.radians(x))


def cos_g(x):
    return math.cos(math.radians(x))


def tan_g(x):
    return math.tan(math.radians(x))


class _Base(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def secante(self, function_latex, x0, x1, angle_mode=None, status=200):
        payload = {'function_latex': function_latex, 'x0': x0, 'x1': x1, 'tolerance': TOL}
        if angle_mode is not None:
            payload['angle_mode'] = angle_mode
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, status, r.data)
        return r.data


class TestGrados(_Base):
    """Los tres casos del issue, con angle_mode='deg'."""

    def test_seno(self):
        data = self.secante(r'\sin(x)-0.5', 20, 40, 'deg')
        self.assertAlmostEqual(data['root'], 30.0, places=7)
        self.assertAlmostEqual(sen_g(data['root']) - 0.5, 0.0, places=10)

    def test_coseno(self):
        data = self.secante(r'\cos(x)', 80, 100, 'deg')
        self.assertAlmostEqual(data['root'], 90.0, places=7)

    def test_tangente(self):
        data = self.secante(r'\tan(x)-1', 40, 50, 'deg')
        self.assertAlmostEqual(data['root'], 45.0, places=7)

    def test_argumento_compuesto(self):
        # sin(2x) = 0.5 con x en grados -> 2x = 30 -> x = 15.
        data = self.secante(r'\sin(2x)-0.5', 10, 20, 'deg')
        self.assertAlmostEqual(data['root'], 15.0, places=7)

    def test_expresion_mixta_solo_convierte_el_argumento_trigonometrico(self):
        # x/2 queda igual; sólo sin(x) pasa a grados.
        data = self.secante(r'\frac{x}{2}+\sin(x)-20', 30, 50, 'deg')
        x = data['root']
        self.assertAlmostEqual(x / 2 + sen_g(x) - 20, 0.0, places=9)
        # Con radianes no sería raíz: el resultado no se obtuvo en rad.
        self.assertGreater(abs(x / 2 + math.sin(x) - 20), 1e-3)

    def test_polinomio_mas_seno_conserva_el_polinomio(self):
        data = self.secante(r'x^{2}+\sin(x)-100', 5, 15, 'deg')
        x = data['root']
        self.assertAlmostEqual(x ** 2 + sen_g(x) - 100, 0.0, places=9)


class TestRadianesSinCambios(_Base):
    """Mismos sistemas en radianes: los valores que devolvía antes."""

    ANTES = [
        (r'\sin(x)-0.5', 20, 40, 52.883476335428185),
        (r'\cos(x)', 80, 100, 69987343.99074548),
        (r'\tan(x)-1', 40, 50, 25.918139392115794),
    ]

    def test_rad_explicito_conserva_el_resultado_previo(self):
        for f, x0, x1, raiz in self.ANTES:
            with self.subTest(f=f):
                self.assertEqual(self.secante(f, x0, x1, 'rad')['root'], raiz)

    def test_parametro_omitido_es_radianes(self):
        for f, x0, x1, raiz in self.ANTES:
            with self.subTest(f=f):
                omitido = self.secante(f, x0, x1)
                self.assertEqual(omitido['root'], raiz)
                self.assertEqual(omitido['table'], self.secante(f, x0, x1, 'rad')['table'])
                self.assertEqual(omitido['angle_mode'], 'rad')

    def test_funcion_sin_trigonometricas_no_depende_del_modo(self):
        rad = self.secante(r'x^{2}-4', 1, 3, 'rad')
        deg = self.secante(r'x^{2}-4', 1, 3, 'deg')
        self.assertAlmostEqual(rad['root'], 2.0, places=8)
        for clave in ('root', 'iterations', 'table', 'error_final'):
            self.assertEqual(rad[clave], deg[clave], clave)


class TestValidacion(_Base):

    def test_angle_mode_invalido_400(self):
        for valor in ('cualquier-cosa', 'DEG', 'grados', ''):
            with self.subTest(valor=valor):
                r = self.client.post(URL, {
                    'function_latex': r'\sin(x)-0.5', 'x0': 20, 'x1': 40,
                    'tolerance': TOL, 'angle_mode': valor,
                }, format='json')
                self.assertEqual(r.status_code, 400)
                self.assertEqual(r.data['error']['code'], 'VALIDATION_ERROR')
                self.assertIn('angle_mode', r.data['error']['message'])

    def test_expresion_invalida_400_controlado(self):
        data = self.secante(r'\sin(', 20, 40, 'deg', status=400)
        self.assertEqual(data['error']['code'], 'SECANT_ERROR')

    def test_secante_horizontal_en_grados_400_controlado(self):
        # cos(-10°) = cos(10°): denominador nulo en la primera iteración.
        data = self.secante(r'\cos(x)', -10, 10, 'deg', status=400)
        self.assertEqual(data['error']['code'], 'SECANT_ERROR')
        self.assertIn('secante', data['error']['message'].lower())

    def test_motor_rechaza_modo_desconocido(self):
        with self.assertRaises(ValueError):
            metodo_secante('sin(x) - 0.5', 20, 40, TOL, modo_angular='grad')


class TestCoherenciaEnGrados(_Base):
    """root, tabla, pasos y conclusión hablan de la misma raíz, en grados."""

    def test_raiz_tabla_pasos_y_conclusion(self):
        data = self.secante(r'\sin(x)-0.5', 20, 40, 'deg')
        raiz = data['root']
        ultima = data['table'][-1]

        self.assertEqual(data['angle_mode'], 'deg')
        self.assertEqual(ultima['x_next'], raiz)
        self.assertEqual(data['conclusion']['root'], raiz)
        self.assertEqual(data['iterations'], len(data['table']))

        # Cada f de la tabla es la función en grados, no en radianes.
        for fila in data['table']:
            for x, fx in ((fila['x_prev'], fila['f_prev']),
                          (fila['x_curr'], fila['f_curr']),
                          (fila['x_next'], fila['f_next'])):
                self.assertAlmostEqual(fx, sen_g(x) - 0.5, places=12)

        # Pasos y conclusión marcan la unidad.
        self.assertIn(r'^\circ', data['conclusion']['latex'])
        self.assertIn(f'{raiz:.6f}', data['conclusion']['latex'])
        self.assertIn(r'^\circ', data['details'][-1]['lines'][0])
        # La función mostrada es la que efectivamente se evaluó.
        self.assertIn('180', data['function_latex'])

    def test_radianes_no_marca_grados(self):
        data = self.secante(r'\sin(x)-0.5', 20, 40, 'rad')
        self.assertNotIn(r'^\circ', data['conclusion']['latex'])
        self.assertNotIn(r'^\circ', data['details'][-1]['lines'][0])


class TestLatexConservaLasLlamadasTrigonometricas(_Base):
    """Revisión de Codex en el PR #27: si latex_a_texto() simplificara en
    radianes antes de que llegue el modo (sin(pi/6) -> 1/2,
    sin(x + pi) -> -sin(x)), 'deg' se aplicaría sobre una expresión ya
    convertida. El parser LaTeX de sympy construye cada llamada sin
    evaluarla, así que la conversión a grados ve el argumento original.
    Estos casos lo fijan de punta a punta."""

    def test_latex_a_texto_no_evalua_valores_especiales(self):
        from api.adapters.latex import latex_a_texto
        self.assertEqual(latex_a_texto(r'x+\sin(\frac{\pi}{6})'), 'x + sin(pi/6)')
        self.assertEqual(latex_a_texto(r'\sin(x+\pi)'), 'sin(pi + x)')
        self.assertEqual(latex_a_texto(r'\sin(\pi)'), 'sin(pi)')

    def test_constante_trigonometrica_en_grados(self):
        # sin(pi/6) con pi/6 ≈ 0.5236 grados, no 1/2: raíz ≈ -0.00914.
        data = self.secante(r'x+\sin(\frac{\pi}{6})', -1, 1, 'deg')
        self.assertAlmostEqual(data['root'], -sen_g(math.pi / 6), places=10)
        self.assertNotAlmostEqual(data['root'], -0.5, places=3)

    def test_argumento_desplazado_por_pi_en_grados(self):
        # sin(x + pi) en grados: pi es 3.14159…, no 180°, así que no vale
        # sin(x + pi) = -sin(x). La raíz cerca de 0 es x = -pi.
        data = self.secante(r'\sin(x+\pi)', 10, 20, 'deg')
        self.assertAlmostEqual(data['root'], -math.pi, places=8)
        self.assertAlmostEqual(sen_g(data['root'] + math.pi), 0.0, places=12)


class TestNuclearSinApi(unittest.TestCase):
    """El modo vive en core/: el CLI o cualquier otro consumidor lo hereda."""

    def test_core_en_grados(self):
        r = metodo_secante('sin(x) - 0.5', 20, 40, TOL, modo_angular='deg')
        self.assertAlmostEqual(r['raiz'], 30.0, places=7)

    def test_core_default_radianes(self):
        self.assertEqual(
            metodo_secante('sin(x) - 0.5', 20, 40, TOL)['raiz'],
            metodo_secante('sin(x) - 0.5', 20, 40, TOL, modo_angular='rad')['raiz'],
        )


if __name__ == '__main__':
    unittest.main()
