import unittest

from core.cramer import CramerMethod
from utils.html_display import frame_to_html
from utils.printMethods import log_step


class TestFrameNoPierdePasos(unittest.TestCase):
    """El frame era un dict indexado por la descripción del paso, así que dos
    pasos con el mismo texto se pisaban y el segundo borraba al primero, sin
    ningún aviso. Estos tests fijan la propiedad que lo impide: N llamadas a
    log_step producen N pasos, pase lo que pase con las descripciones."""

    def test_n_llamadas_producen_n_pasos(self):
        frame = []
        for i in range(10):
            log_step(frame, f"Paso {i}", [[1.0]], tag="t")
        self.assertEqual(len(frame), 10)

    def test_descripciones_repetidas_no_se_pisan(self):
        # El caso exacto del bug: un label constante repetido.
        frame = []
        for _ in range(4):
            log_step(frame, "Sarrus - Matriz Extendida", [[1.0]], tag="sarrus")
        self.assertEqual(len(frame), 4)

    def test_pasos_identicos_en_todo_siguen_siendo_distintos(self):
        # Ni siquiera con texto, matriz, det y tag iguales deben colapsar.
        frame = []
        for _ in range(3):
            log_step(frame, "mismo", [[2.0]], det=5.0, tag="igual")
        self.assertEqual(len(frame), 3)

    def test_se_preserva_el_orden_de_registro(self):
        frame = []
        for nombre in ["primero", "segundo", "tercero"]:
            log_step(frame, nombre, None)
        self.assertEqual([p["text"] for p in frame], ["primero", "segundo", "tercero"])

    def test_index_es_correlativo(self):
        frame = []
        for i in range(5):
            log_step(frame, f"p{i}", None)
        self.assertEqual([p["index"] for p in frame], [0, 1, 2, 3, 4])


class TestExtraNoReintroduceLaColision(unittest.TestCase):
    """`extra` es el campo donde van los datos propios de cada método (triples
    de Sarrus, menores, cofactores). Va DENTRO de cada paso, no en un dict
    compartido indexado por descripción: es justamente la forma que causaba el
    bug original. Estos tests fijan que no vuelva por esa puerta."""

    def test_cada_paso_conserva_su_propio_extra(self):
        frame = []
        log_step(frame, "Diagonales", None, extra={"triples": [1, 2, 3]})
        log_step(frame, "Diagonales", None, extra={"triples": [4, 5, 6]})

        self.assertEqual(len(frame), 2)
        self.assertEqual(frame[0]["extra"]["triples"], [1, 2, 3])
        self.assertEqual(frame[1]["extra"]["triples"], [4, 5, 6])

    def test_extra_ausente_queda_en_none(self):
        frame = []
        log_step(frame, "sin extra", None)
        self.assertIsNone(frame[0]["extra"])


class TestCramerRegistraTodosLosDeterminantes(unittest.TestCase):
    """Cramer calcula n+1 determinantes (el de A y uno por variable) y todos
    registraban el mismo label constante. Con el frame como dict sobrevivía
    sólo el último: el procedimiento mostraba una expansión de Sarrus en vez de
    cuatro. Este test es el que hubiera atrapado el bug."""

    def setUp(self):
        self.A = [[3.0, 3.0, -1.0], [1.0, 3.0, 2.0], [3.0, -2.0, 3.0]]
        self.b = [-2.0, 2.0, 1.0]

    def test_no_se_pierde_ningun_paso_al_resolver(self):
        cramer = CramerMethod([f[:] for f in self.A], list(self.b))
        llamadas = []

        import utils.printMethods as pm
        import core.cramer as cramer_mod

        original = pm.log_step

        def contando(frame, step, matrix_state, det=None, tag=None, extra=None):
            llamadas.append(step)
            return original(frame, step, matrix_state, det, tag, extra)

        cramer_mod.log_step = contando
        try:
            cramer.solve()
        finally:
            cramer_mod.log_step = original

        self.assertEqual(len(cramer.frame), len(llamadas))

    def test_el_html_muestra_las_n_mas_1_expansiones_de_sarrus(self):
        cramer = CramerMethod([f[:] for f in self.A], list(self.b))
        cramer.solve()
        # show_det ya no necesita desactivarse: frame_to_html tolera que
        # Cramer registre det ya formateado como str (ver TestFrameToHtmlToleraDetString).
        html = frame_to_html(cramer.frame)

        self.assertEqual(html.count("Sarrus - Matriz Extendida"), len(self.A) + 1)


class TestFrameToHtmlToleraDetString(unittest.TestCase):
    """frame_to_html llamaba format_number(det_val) sin protección, y
    format_number hace `num - int(num)`: revienta con TypeError si det es un
    str. Cramer registra det ya formateado como string en ~10 llamadas (ej.
    core/cramer.py:81, det=format_number(det)), así que cualquier frame de
    Cramer reventaba el render HTML. print_frame ya toleraba esto con un
    try/except; frame_to_html ahora replica el mismo criterio: intenta
    formatear, y si falla, muestra el valor tal cual llegó."""

    def test_det_string_no_revienta_el_render(self):
        frame = [{"text": "paso", "matrix": None, "det": "5/2", "tag": None, "extra": None}]
        html = frame_to_html(frame)  # no debe lanzar
        self.assertIn("5/2", html)

    def test_det_numerico_se_sigue_formateando_igual(self):
        frame = [{"text": "paso", "matrix": None, "det": 5.0, "tag": None, "extra": None}]
        html = frame_to_html(frame)
        self.assertIn("Determinante: 5", html)
        self.assertNotIn("Determinante: 5.0", html)

    def test_cramer_real_no_revienta_con_show_det_por_defecto(self):
        cramer = CramerMethod(
            [[3.0, 3.0, -1.0], [1.0, 3.0, 2.0], [3.0, -2.0, 3.0]], [-2.0, 2.0, 1.0]
        )
        cramer.solve()
        html = frame_to_html(cramer.frame)  # no debe lanzar TypeError
        self.assertIn("Determinante:", html)


if __name__ == "__main__":
    unittest.main()
