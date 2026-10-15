"""
Clasificación de sistemas por la regla de Cramer, con foco en det(A) = 0.

Con det(A) = 0 la regla de Cramer sólo prueba UNA implicación:

    sistema compatible  =>  det(Aᵢ) = 0 para todo i

(si x es solución, b = Σ xⱼ·aⱼ y, por multilinealidad del determinante,
det(Aᵢ) = xᵢ·det(A) = 0). Por contrarrecíproca, algún det(Aᵢ) ≠ 0 garantiza
que el sistema es inconsistente. La vuelta NO vale: que todos los det(Aᵢ)
sean cero no garantiza compatibilidad. Contraejemplo mínimo: A = 0, b ≠ 0
(0 = 1), donde cada Aᵢ tiene n-1 columnas nulas y su determinante es 0.

Esos casos los decide el teorema de Rouché–Frobenius comparando
rango(A) con rango([A|b]). Los tests de abajo fijan que:

- la clasificación es la correcta en los casos únicos, inconsistentes e
  infinitos, 2×2 y 3×3, incluidos los que Cramer no puede decidir;
- cuando algún det(Aᵢ) ≠ 0 decide la propia regla (no se corre el análisis
  de rangos), y cuando todos son cero se recurre al análisis de rangos y
  queda registrado en el frame;
- core/, la API REST y Gauss-Jordan coinciden en el estado.
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

URL = '/api/v1/matrix/reduce'

# (nombre, A, b, status_esperado, ¿lo decide la propia regla de Cramer?)
#
# La última columna dice si el caso se resuelve con determinantes solos
# (det(A) ≠ 0, o det(A) = 0 con algún det(Aᵢ) ≠ 0) o si hace falta el
# análisis de rangos (det(A) = 0 y todos los det(Aᵢ) = 0).
CASOS = [
    # --- solución única ------------------------------------------------
    ('2x2_unica', [[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0], 'unique', True),
    ('3x3_unica', [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]], [4.0, 5.0, 6.0], 'unique', True),

    # --- 2×2 inconsistentes -------------------------------------------
    # rectas paralelas: det(A₁) = -1 ≠ 0, Cramer lo decide solo.
    ('2x2_inconsistente_paralelas', [[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0], 'inconsistent', True),
    # A = 0, b ≠ 0: 0 = 1. det(A₁) = det(A₂) = 0 -> Cramer no decide.
    ('2x2_inconsistente_A_nula', [[0.0, 0.0], [0.0, 0.0]], [1.0, 0.0], 'inconsistent', False),

    # --- 2×2 infinitas --------------------------------------------------
    ('2x2_infinitas_no_homogeneo', [[1.0, 2.0], [2.0, 4.0]], [3.0, 6.0], 'infinite', False),
    ('2x2_infinitas_homogeneo', [[1.0, 2.0], [2.0, 4.0]], [0.0, 0.0], 'infinite', False),

    # --- 3×3 singulares incompatibles ----------------------------------
    # El caso del reporte: A = 0, b = (1,0,0) -> 0 = 1.
    ('3x3_inconsistente_A_nula', [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [1.0, 0.0, 0.0], 'inconsistent', False),
    # rango(A) = 1 (filas proporcionales) pero b no es proporcional:
    # x+y+z = 1 y 3x+3y+3z = 4 son planos paralelos. rango([A|b]) = 2.
    ('3x3_inconsistente_rango_1', [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]], [1.0, 2.0, 4.0], 'inconsistent', False),
    # rango(A) = 2: con rango n-1 sí alcanza Cramer (algún det(Aᵢ) ≠ 0).
    ('3x3_inconsistente_rango_2', [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], [1.0, 1.0, 0.0], 'inconsistent', True),

    # --- 3×3 singulares compatibles ------------------------------------
    ('3x3_infinitas_rango_1', [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]], [1.0, 2.0, 3.0], 'infinite', False),
    ('3x3_infinitas_rango_2', [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], [6.0, 15.0, 24.0], 'infinite', False),
    ('3x3_infinitas_A_y_b_nulos', [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [0.0, 0.0, 0.0], 'infinite', False),
]


def _resolver(A, b):
    solver = CramerMethod([row[:] for row in A], list(b))
    return solver, solver.solve()


class TestCramerClasificaBienLosSistemasSingulares(unittest.TestCase):
    """core/cramer.py devuelve el estado matemáticamente correcto."""

    def test_status_de_cada_caso(self):
        for nombre, A, b, status, _ in CASOS:
            with self.subTest(caso=nombre):
                _, r = _resolver(A, b)
                self.assertEqual(r['status'], status)

    def test_regresion_A_nula_b_no_nulo_es_inconsistente(self):
        # El caso exacto del reporte. Antes del fix salía 'infinite': los
        # cuatro determinantes valen 0 y la rama "todos cero" concluía
        # infinitas soluciones de un sistema que dice 0 = 1.
        solver, r = _resolver([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [1.0, 0.0, 0.0])
        dets = [solver.calculate_determinant(solver.create_cramer_matrix(c)) for c in range(3)]
        self.assertEqual(r['determinant'], 0)
        self.assertEqual(dets, [0.0, 0.0, 0.0])
        self.assertEqual(r['status'], 'inconsistent')

    def test_sin_solucion_unica_conserva_el_shape(self):
        # Mismo contrato que antes del fix: solution None y sin clasificar
        # variables (eso sigue siendo trabajo de Gauss / Gauss-Jordan).
        for nombre, A, b, status, _ in CASOS:
            if status == 'unique':
                continue
            with self.subTest(caso=nombre):
                _, r = _resolver(A, b)
                self.assertIsNone(r['solution'])
                self.assertEqual(r['basic_vars'], [])
                self.assertEqual(r['free_vars'], [])
                self.assertEqual(set(r), {'status', 'solution', 'basic_vars', 'free_vars', 'determinant'})

    def test_solucion_unica_satisface_el_sistema(self):
        for nombre, A, b, status, _ in CASOS:
            if status != 'unique':
                continue
            with self.subTest(caso=nombre):
                _, r = _resolver(A, b)
                for fila, bi in zip(A, b):
                    self.assertAlmostEqual(sum(a * x for a, x in zip(fila, r['solution'])), bi, places=9)


class TestCramerRegistraQuienDecide(unittest.TestCase):
    """El frame dice si clasificó la regla de Cramer o el análisis de rangos."""

    def _tags(self, A, b):
        solver, r = _resolver(A, b)
        return [st['tag'] for st in solver.frame], solver.frame, r

    def test_el_analisis_de_rangos_aparece_solo_cuando_cramer_no_decide(self):
        for nombre, A, b, _, decide_cramer in CASOS:
            with self.subTest(caso=nombre):
                tags, _, _ = self._tags(A, b)
                if decide_cramer:
                    self.assertNotIn('rank_check', tags)
                else:
                    self.assertIn('rank_check', tags)

    def test_el_ultimo_paso_coincide_con_el_status(self):
        for nombre, A, b, status, _ in CASOS:
            if status == 'unique':
                continue
            with self.subTest(caso=nombre):
                tags, _, r = self._tags(A, b)
                self.assertEqual(tags[-1], r['status'])

    def test_el_paso_de_rangos_muestra_la_matriz_aumentada(self):
        A, b = [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]], [1.0, 2.0, 4.0]
        _, frame, _ = self._tags(A, b)
        paso = next(st for st in frame if st['tag'] == 'rank_check')
        self.assertEqual(paso['matrix'], [row + [bi] for row, bi in zip(A, b)])
        self.assertIn('rango(A) = 1', paso['text'])
        self.assertIn('rango([A|b]) = 2', paso['text'])

    def test_ningun_paso_afirma_que_todos_cero_implica_infinitas(self):
        # La afirmación falsa que tenía el frame antes del fix.
        for nombre, A, b, _, _ in CASOS:
            with self.subTest(caso=nombre):
                _, frame, _ = self._tags(A, b)
                for st in frame:
                    self.assertNotIn('todos cero -> infinitas', st['text'])


class TestCramerCoreApiYGaussCoinciden(unittest.TestCase):
    """Mismo estado en core/, en la API con method=cramer y con Gauss-Jordan."""

    def setUp(self):
        self.client = APIClient()

    def _post(self, method, A, b):
        r = self.client.post(URL, {'method': method, 'A': A, 'b': b}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        return r.data

    def test_core_y_api_coinciden(self):
        for nombre, A, b, status, _ in CASOS:
            with self.subTest(caso=nombre):
                solver, directo = _resolver(A, b)
                data = self._post('cramer', A, b)
                summary = data['summary']
                self.assertEqual(summary['status'], directo['status'])
                self.assertEqual(summary['solution_type'], directo['status'])
                self.assertEqual(summary['status'], status)
                self.assertEqual(summary['is_singular'], status != 'unique')
                self.assertEqual(len(data['result']['determinants']), len(A) + 1)
                self.assertEqual(len(data['steps']['frame']['states']), len(solver.frame))
                if status == 'unique':
                    for va, vd in zip(summary['solution'], directo['solution']):
                        self.assertAlmostEqual(va, vd, places=9)
                else:
                    self.assertIsNone(summary['solution'])

    def test_cramer_y_gauss_jordan_clasifican_igual(self):
        for nombre, A, b, status, _ in CASOS:
            with self.subTest(caso=nombre):
                cramer = self._post('cramer', A, b)['summary']['status']
                gj = self._post('gauss-jordan', A, b)['summary']['status']
                self.assertEqual(cramer, gj)

    def test_el_summary_de_cramer_sigue_sin_rangos(self):
        # Contrato de la Fase 7 (ver docstring de api/adapters/reduce.py): el
        # análisis de rangos auxiliar se ve en los pasos, no se agrega al
        # summary de Cramer.
        data = self._post('cramer', [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [1.0, 0.0, 0.0])
        self.assertNotIn('rank', data['summary'])
        self.assertNotIn('ranks', data['summary'])


if __name__ == '__main__':
    unittest.main()
