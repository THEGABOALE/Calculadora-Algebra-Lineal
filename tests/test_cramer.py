import unittest

from core.cramer import CramerMethod
from core.matrix_tools import determinant as mt_determinant


class TestCramerTresMetodos(unittest.TestCase):
    """Sarrus, cofactores y matrix_tools.determinant deben coincidir sobre la
    misma matriz: es la comparación que compare_determinant_methods hace por
    consola, automatizada como assertAlmostEqual."""

    def setUp(self):
        # determinante conocido = 1
        self.A = [[1.0, 2.0, 3.0], [0.0, 1.0, 4.0], [5.0, 6.0, 0.0]]
        self.cramer = CramerMethod(self.A, [1.0, 1.0, 1.0])

    def test_sarrus_cofactores_y_matrix_tools_coinciden(self):
        det_sarrus = self.cramer.calculate_determinant_sarrus(self.A)
        self.cramer.frame = {}
        det_cofactores = self.cramer.calculate_determinant_cofactors(self.A)
        det_mt = mt_determinant(self.A)

        self.assertAlmostEqual(det_sarrus, det_cofactores, delta=1e-10)
        self.assertAlmostEqual(det_sarrus, det_mt, delta=1e-10)
        self.assertAlmostEqual(det_cofactores, det_mt, delta=1e-10)
        self.assertAlmostEqual(det_sarrus, 1.0, delta=1e-10)

    def test_cramer_basico_tambien_coincide(self):
        # calculate_determinant() (el método "básico", no tocado en esta fase)
        # es el tercer método que compare_determinant_methods pone a competir.
        det_basico = self.cramer.calculate_determinant(self.A, show_sarrus=False)
        det_mt = mt_determinant(self.A)
        self.assertAlmostEqual(det_basico, det_mt, delta=1e-10)

    def test_cofactores_coincide_en_4x4(self):
        # Sarrus sólo cubre 3x3; cofactores es el único de los tres que
        # también resuelve n > 3, así que se compara aparte.
        A4 = [[1.0, 0.0, 0.0, 2.0], [0.0, 1.0, 0.0, 3.0],
              [0.0, 0.0, 1.0, 4.0], [2.0, 3.0, 4.0, 5.0]]
        c4 = CramerMethod(A4, [1.0, 1.0, 1.0, 1.0])
        det_cofactores = c4.calculate_determinant_cofactors(A4)
        det_mt = mt_determinant(A4)
        self.assertAlmostEqual(det_cofactores, det_mt, delta=1e-10)


class TestSarrusRechazaNoTresPorTres(unittest.TestCase):
    def test_rechaza_2x2(self):
        c = CramerMethod([[1.0, 0.0], [0.0, 1.0]], [1.0, 1.0])
        with self.assertRaises(ValueError):
            c.calculate_determinant_sarrus([[1.0, 0.0], [0.0, 1.0]])

    def test_rechaza_4x4(self):
        A4 = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0],
              [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        c = CramerMethod(A4, [1.0, 1.0, 1.0, 1.0])
        with self.assertRaises(ValueError):
            c.calculate_determinant_sarrus(A4)


class TestRunCramerAlias(unittest.TestCase):
    """C3: run_crammer debe seguir resolviendo, como alias de run_cramer."""

    def test_alias_es_el_mismo_objeto(self):
        from cli.method_runners import run_cramer, run_crammer
        self.assertIs(run_crammer, run_cramer)


if __name__ == "__main__":
    unittest.main()
