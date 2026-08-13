"""
Tests de POST /api/v1/matrix/reduce con method='cramer'.

Cramer entra por `matrix/reduce` y no por `matrix/determinant`: resuelve un
sistema (pide A y b), no calcula un determinante suelto. La Fase 3 había
dejado `method='cramer'` rechazado con 400 explícito en
MatrixDeterminantSerializer justamente para no repetir el alias falso del
repo del que se portó el frontend, donde `determinant_cramer(A)` era
literalmente `return determinant_cofactors(A)`. Ese rechazo se verifica acá
también: implementar Cramer de verdad no lo vuelve válido en el otro
endpoint.

El corazón de esta fase es TestCramerNMasUnDeterminantes: la respuesta tiene
que traer los **n+1** determinantes (det(A) más uno por variable), no uno
solo. Es la regresión que arregló el commit 3b477fc al pasar el frame de
dict indexado por descripción a lista ordenada -- con el dict, los n pasos
"Matriz Cramer para xᵢ" se pisaban entre sí y sobrevivía uno.
"""
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

from core.cramer import CramerMethod
from core.matrix_tools import determinant as mt_determinant

URL = '/api/v1/matrix/reduce'
URL_DET = '/api/v1/matrix/determinant'

# (nombre, A, b, status_esperado)
CASOS = [
    ('3x3_unica', [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0], 'unique'),
    ('3x3_det_uno', [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]], [1.0, 1.0, 1.0], 'unique'),
    ('2x2_unica', [[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0], 'unique'),
    ('2x2_inconsistente', [[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0], 'inconsistent'),
    ('2x2_infinitas', [[1.0, 2.0], [2.0, 4.0]], [0.0, 0.0], 'infinite'),
    ('4x4_unica', [[1.0, 0.0, 0.0, 2.0], [0.0, 1.0, 0.0, 3.0],
                   [0.0, 0.0, 1.0, 4.0], [2.0, 3.0, 4.0, 5.0]], [1.0, 1.0, 1.0, 1.0], 'unique'),
]


def _resolver_directo(A, b):
    solver = CramerMethod([row[:] for row in A], list(b))
    resultado = solver.solve()
    return solver, resultado


class TestCramerParidadConElMotor(unittest.TestCase):
    """La respuesta del endpoint contra CramerMethod.solve() llamado directo."""

    def setUp(self):
        self.client = APIClient()

    def _comparar(self, A, b, status_esperado):
        r = self.client.post(URL, {'method': 'cramer', 'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        summary = r.data['summary']

        solver, directo = _resolver_directo(A, b)

        self.assertEqual(summary['status'], status_esperado)
        self.assertEqual(summary['status'], directo['status'])
        self.assertAlmostEqual(summary['determinant'], directo['determinant'], places=9)
        # det(A) por Cramer tiene que coincidir con el de matrix_tools, que es
        # el tercer motor que tests/test_cramer.py ya pone a competir contra
        # Sarrus y cofactores.
        self.assertAlmostEqual(summary['determinant'], mt_determinant(A), places=9)

        if status_esperado == 'unique':
            for va, vd in zip(summary['solution'], directo['solution']):
                self.assertAlmostEqual(va, vd, places=9)
        else:
            # core devuelve 'solution': 'Crammer' (un literal, no una
            # solución) en la rama de infinitas. El adaptador no propaga esa
            # cadena: sin solución única, `solution` es null.
            self.assertIsNone(summary['solution'])

        # Mismo criterio que el resto de la API: los pasos que salen son
        # tantos como pasos tiene el frame real, ni fijos ni recortados.
        self.assertEqual(len(r.data['steps']['frame']['states']), len(solver.frame))

    def test_todos_los_casos(self):
        for nombre, A, b, status in CASOS:
            with self.subTest(caso=nombre):
                self._comparar(A, b, status)

    def test_solucion_unica_satisface_el_sistema(self):
        A, b = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0]
        r = self.client.post(URL, {'method': 'cramer', 'A': A, 'b': b}, format='json')
        x = r.data['summary']['solution']
        for fila, esperado in zip(A, b):
            self.assertAlmostEqual(sum(c * xi for c, xi in zip(fila, x)), esperado, places=9)


class TestCramerNMasUnDeterminantes(unittest.TestCase):
    """La respuesta trae det(A) MÁS uno por variable: n+1, no uno."""

    def setUp(self):
        self.client = APIClient()

    def _determinantes(self, A, b):
        r = self.client.post(URL, {'method': 'cramer', 'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        return r.data['result']['determinants']

    def test_3x3_trae_cuatro_determinantes(self):
        dets = self._determinantes([[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0])
        self.assertEqual(len(dets), 4)

    def test_4x4_trae_cinco_determinantes(self):
        A = [[1.0, 0.0, 0.0, 2.0], [0.0, 1.0, 0.0, 3.0],
             [0.0, 0.0, 1.0, 4.0], [2.0, 3.0, 4.0, 5.0]]
        dets = self._determinantes(A, [1.0, 1.0, 1.0, 1.0])
        self.assertEqual(len(dets), 5)

    def test_el_primero_es_det_a_y_el_resto_uno_por_variable(self):
        A, b = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0]
        dets = self._determinantes(A, b)
        self.assertEqual(dets[0]['variable'], None)
        self.assertAlmostEqual(dets[0]['value'], mt_determinant(A), places=9)
        self.assertEqual([d['variable'] for d in dets[1:]], [0, 1, 2])

    def test_cada_determinante_de_cramer_dividido_det_a_da_la_variable(self):
        # La regla de Cramer en sí: xᵢ = det(Aᵢ)/det(A). Si los n+1
        # determinantes que se muestran no cumplen eso, se está mostrando
        # cualquier cosa aunque la solución esté bien.
        A, b = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0]
        r = self.client.post(URL, {'method': 'cramer', 'A': A, 'b': b}, format='json')
        dets = r.data['result']['determinants']
        solucion = r.data['summary']['solution']
        det_a = dets[0]['value']
        for det_i, xi in zip(dets[1:], solucion):
            self.assertAlmostEqual(det_i['value'] / det_a, xi, places=9)

    def test_sistema_singular_igual_trae_los_n_mas_1(self):
        # Con det(A)=0 no hay solución, pero los determinantes de Cramer se
        # calculan igual: son justamente los que distinguen inconsistente de
        # infinitas. Mostrar sólo det(A) escondería esa distinción.
        dets = self._determinantes([[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0])
        self.assertEqual(len(dets), 3)

    def test_los_determinantes_aparecen_en_los_pasos(self):
        # No alcanza con el bloque compacto: el procedimiento paso a paso
        # también tiene que mostrar una matriz de Cramer por variable.
        A, b = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0]
        r = self.client.post(URL, {'method': 'cramer', 'A': A, 'b': b}, format='json')
        states = r.data['steps']['frame']['states']
        con_det = [st for st in states if st['tag'].startswith('cramer_x')]
        self.assertEqual(len(con_det), 3)
        for st in con_det:
            self.assertIsNotNone(st['det'])


class TestCramerEnvelopeDePasos(unittest.TestCase):
    """Cramer usa el envelope frame.states, no la lista plana de gauss."""

    def setUp(self):
        self.client = APIClient()

    def test_steps_es_envelope_con_states_y_text_steps(self):
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[2.0, 1.0], [1.0, -1.0]], 'b': [5.0, 1.0],
        }, format='json')
        steps = r.data['steps']
        self.assertIn('frame', steps)
        self.assertIn('states', steps['frame'])
        self.assertEqual(len(steps['text_steps']), len(steps['frame']['states']))

    def test_gauss_sigue_devolviendo_lista_plana(self):
        # El cambio de shape es sólo para cramer: gauss no se toca.
        r = self.client.post(URL, {
            'method': 'gauss', 'A': [[2.0, 1.0], [1.0, -1.0]], 'b': [5.0, 1.0],
        }, format='json')
        self.assertIsInstance(r.data['steps'], list)

    def test_el_metodo_viaja_en_input_para_que_el_frontend_elija_el_render(self):
        # ResultPretty.tsx elige la rama de render con result.input.method.
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[2.0, 1.0], [1.0, -1.0]], 'b': [5.0, 1.0],
        }, format='json')
        self.assertEqual(r.data['input']['method'], 'cramer')


class TestCramerValidacion(unittest.TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_matriz_no_cuadrada_400(self):
        # CramerMethod.__init__ levanta ValueError; la vista lo traduce a 400
        # con el mensaje del motor, no un 500.
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], 'b': [1.0, 2.0],
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('cuadrada', str(r.data).lower())

    def test_b_de_largo_distinto_400(self):
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[1.0, 2.0], [3.0, 4.0]], 'b': [1.0],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_acepta_ab_aumentada_igual_que_gauss(self):
        # El serializer parte Ab en A y b antes del adaptador: cramer hereda
        # esa entrada sin hacer nada.
        A, b = [[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0]
        Ab = [[2.0, 1.0, 5.0], [1.0, -1.0, 1.0]]
        r_sep = self.client.post(URL, {'method': 'cramer', 'A': A, 'b': b}, format='json')
        r_ab = self.client.post(URL, {'method': 'cramer', 'Ab': Ab}, format='json')
        self.assertEqual(r_ab.status_code, 200, r_ab.data)
        for va, vd in zip(r_sep.data['summary']['solution'], r_ab.data['summary']['solution']):
            self.assertAlmostEqual(va, vd, places=9)


class TestCramerSigueRechazadoEnDeterminant(unittest.TestCase):
    """Implementarlo en reduce no lo vuelve válido en determinant."""

    def setUp(self):
        self.client = APIClient()

    def test_determinant_con_cramer_400(self):
        r = self.client.post(URL_DET, {
            'method': 'cramer', 'A': [[1.0, 2.0], [3.0, 4.0]],
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_el_mensaje_apunta_a_matrix_reduce(self):
        r = self.client.post(URL_DET, {
            'method': 'cramer', 'A': [[1.0, 2.0], [3.0, 4.0]],
        }, format='json')
        self.assertIn('reduce', str(r.data))


class TestCramerVariablesSoloCuandoHaySolucionUnica(unittest.TestCase):
    """Con det(A)=0, Cramer no clasifica variables -- y no debe fingir que sí."""

    def setUp(self):
        self.client = APIClient()

    def test_unica_reporta_todas_las_variables_como_basicas(self):
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[2.0, 1.0], [1.0, -1.0]], 'b': [5.0, 1.0],
        }, format='json')
        self.assertEqual(r.data['summary']['basic_vars'], [0, 1])
        self.assertEqual(r.data['summary']['free_vars'], [])

    def test_infinitas_no_declara_todas_las_variables_basicas(self):
        # core devuelve basic_vars=[0..n-1] y free_vars=[] también acá, que
        # para un sistema con infinitas soluciones es falso: hay variables
        # libres, sólo que la regla de Cramer no las identifica -- eso lo
        # hace Gauss. Propagarlo pintaría "Variables básicas: x₁, x₂" en la
        # UI de un sistema que no tiene solución única.
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[1.0, 2.0], [2.0, 4.0]], 'b': [0.0, 0.0],
        }, format='json')
        self.assertEqual(r.data['summary']['basic_vars'], [])
        self.assertEqual(r.data['summary']['free_vars'], [])

    def test_inconsistente_tampoco(self):
        r = self.client.post(URL, {
            'method': 'cramer', 'A': [[1.0, 1.0], [1.0, 1.0]], 'b': [1.0, 2.0],
        }, format='json')
        self.assertEqual(r.data['summary']['basic_vars'], [])


if __name__ == '__main__':
    unittest.main()
