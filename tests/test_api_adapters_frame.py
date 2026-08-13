"""
api/adapters/frame.py es la pieza que todas las fases de la API van a reusar
para traducir un frame de core/ (lista de Step) al contrato web. Se verifica
contra un frame real de 15 pasos (core/matrix_tools.inverse sobre una 3x3),
no sólo contra un caso trivial de un paso -- un caso de un solo paso no
puede exponer un desalineamiento entre step_states y text_steps porque no
hay forma de que un único elemento esté "corrido" respecto de otro.
"""
import os
import sys
import unittest

_LAC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'linear_algebra_calculator')
sys.path.insert(0, _LAC_DIR)

from core.matrix_tools import inverse
from api.adapters.frame import frame_to_steps, frame_to_step_states_envelope


def _frame_de_inversa_3x3():
    frame = []
    A = [[2.0, 1.0, 1.0], [1.0, 3.0, 2.0], [1.0, 0.0, 0.0]]
    inverse(A, frame=frame)
    return frame


class TestFrameToSteps(unittest.TestCase):
    def test_conserva_la_cantidad_de_pasos(self):
        frame = _frame_de_inversa_3x3()
        steps = frame_to_steps(frame)
        self.assertEqual(len(steps), len(frame))
        self.assertEqual(len(steps), 15)

    def test_text_pasa_a_operation_sin_perder_nada_mas(self):
        frame = _frame_de_inversa_3x3()
        steps = frame_to_steps(frame)
        for step, original in zip(steps, frame):
            self.assertEqual(step['operation'], original['text'])
            self.assertEqual(step['matrix'], original['matrix'])
            self.assertEqual(step['det'], original['det'])
            self.assertEqual(step['tag'], original['tag'])
            self.assertEqual(step['index'], original['index'])

    def test_ultimo_paso_trae_el_determinante(self):
        # El último paso de inverse() es el que registra det(A); es el único
        # con 'det' no nulo en este caso, así que sirve para confirmar que
        # el valor llega hasta el step correcto y no a otro por error de
        # índice.
        steps = frame_to_steps(_frame_de_inversa_3x3())
        self.assertEqual(steps[-1]['tag'], 'det')
        self.assertEqual(steps[-1]['det'], -1.0)
        self.assertIsNone(steps[0]['det'])

    def test_frame_vacio_da_lista_vacia(self):
        self.assertEqual(frame_to_steps([]), [])
        self.assertEqual(frame_to_steps(None), [])


class TestFrameToStepStatesEnvelope(unittest.TestCase):
    def test_step_states_y_text_steps_tienen_la_misma_longitud(self):
        env = frame_to_step_states_envelope(_frame_de_inversa_3x3())
        self.assertEqual(len(env['frame']['step_states']), len(env['text_steps']))
        self.assertEqual(len(env['text_steps']), 15)

    def test_alineamiento_por_indice_en_un_paso_intermedio(self):
        # El paso 4 (0-indexado) es "F2 -> F2 / 5/2": escala la fila 2. Si
        # step_states y text_steps vinieran de fuentes distintas en vez de
        # derivarse del mismo frame, este es el tipo de caso donde un
        # desalineamiento se notaría (matriz de un paso con el texto de
        # otro).
        env = frame_to_step_states_envelope(_frame_de_inversa_3x3())
        self.assertEqual(env['text_steps'][4], 'F2 -> F2 / 5/2')
        self.assertEqual(env['frame']['step_states'][4]['tag'], 'scale')
        fila_2_escalada = env['frame']['step_states'][4]['matrix'][1]
        # tras F2 -> F2/(5/2), la fila 2 debe tener un 1 en la columna del
        # pivote (columna 1, índice 1).
        self.assertAlmostEqual(fila_2_escalada[1], 1.0, places=9)

    def test_envelope_vacio(self):
        env = frame_to_step_states_envelope([])
        self.assertEqual(env, {'frame': {'step_states': []}, 'text_steps': []})


if __name__ == '__main__':
    unittest.main()
