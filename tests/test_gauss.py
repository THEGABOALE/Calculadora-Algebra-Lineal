import unittest

from core.gauss import GaussMethod


def resolver(A, b):
    """Contrato de dos pasos: gauss_method() elimina, solve_and_log() analiza."""
    g = GaussMethod([fila[:] for fila in A], list(b))
    g.gauss_method()
    resultado = g.solve_and_log()
    return g, resultado


class TestGaussPivoteo(unittest.TestCase):
    """El pivoteo debe ser por filas. Un swap de columnas permutaría las
    variables sin dejar rastro para deshacerlo, y estos casos lo expondrían."""

    def test_pivote_nulo_exige_intercambio_de_filas(self):
        #  y +  z = 3
        # x     + z = 4
        # x +  y     = 5     -> A[0][0] = 0, obliga a intercambiar filas
        A = [[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]]
        b = [3.0, 4.0, 5.0]
        g, r = resolver(A, b)

        self.assertEqual(r["status"], "unique")
        for obtenido, esperado in zip(r["solution"], [3.0, 2.0, 1.0]):
            self.assertAlmostEqual(obtenido, esperado, places=9)

    def test_no_se_intercambian_columnas(self):
        # 2x +  y = 5 ; 4x + 3y = 11.  El pivoteo viejo elegía la columna 2
        # porque su valor estaba más cerca de 1, y devolvía [1, 2].
        A = [[2.0, 1.0], [4.0, 3.0]]
        b = [5.0, 11.0]
        g, r = resolver(A, b)

        for obtenido, esperado in zip(r["solution"], [2.0, 1.0]):
            self.assertAlmostEqual(obtenido, esperado, places=9)
        tags = {v["tag"] for v in g.frame.values()}
        self.assertNotIn("swap_cols", tags)

    def test_la_columna_b_nunca_entra_en_los_coeficientes(self):
        # 2x + 3y = 1 ; 4x + 5y = 9.  El pivoteo viejo buscaba columnas
        # alternativas en range(col+1, columnas), que en una aumentada incluye
        # la columna de b: llegaba a hacer "Columna 1 <-> Columna 3".
        A = [[2.0, 3.0], [4.0, 5.0]]
        b = [1.0, 9.0]
        g, r = resolver(A, b)

        for obtenido, esperado in zip(r["solution"], [11.0, -7.0]):
            self.assertAlmostEqual(obtenido, esperado, places=9)
        tags = {v["tag"] for v in g.frame.values()}
        self.assertNotIn("swap_cols", tags)

    def test_solucion_verifica_el_sistema(self):
        A = [[0.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 0.0]]
        b = [3.0, 4.0, 5.0]
        _, r = resolver(A, b)
        x = r["solution"]
        for fila, termino in zip(A, b):
            self.assertAlmostEqual(sum(c * v for c, v in zip(fila, x)), termino, places=9)


class TestGaussContrato(unittest.TestCase):
    def test_solve_and_log_exige_matriz_aumentada(self):
        g = GaussMethod([[1.0, 2.0], [3.0, 4.0]], None)
        with self.assertRaises(RuntimeError):
            g.solve_and_log()


if __name__ == "__main__":
    unittest.main()
