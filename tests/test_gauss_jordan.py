import unittest

from core.gauss_jordan import GaussJordanMethod


def resolver(A, b):
    """Contrato de dos pasos: run() elimina, solve_and_log() analiza."""
    g = GaussJordanMethod([fila[:] for fila in A], list(b))
    g.run()
    resultado = g.solve_and_log()
    tags = {v["tag"] for v in g.frame.values()}
    return g, resultado, tags


class TestGaussJordanHomogeneidad(unittest.TestCase):
    """Análisis homogéneo / no homogéneo que llegó por el linaje de HomoNohomo."""

    def test_homogeneo_solucion_unica_trivial(self):
        # 2x + y = 0 ; x - y = 0  -> rango 2 = n, sólo la solución trivial
        A = [[2.0, 1.0], [1.0, -1.0]]
        b = [0.0, 0.0]
        g, r, tags = resolver(A, b)

        self.assertTrue(g.is_homogeneous)
        self.assertEqual(r["status"], "unique")
        self.assertEqual(r["tipo_sistema"], "homogéneo")
        for valor in r["solution"]:
            self.assertAlmostEqual(valor, 0.0, places=9)

        self.assertIn("homogeneous_unique", tags)
        self.assertIn("trivial_solution", tags)
        # sin variables libres no hay forma paramétrica
        self.assertIsNone(r["parametric_solution"])

    def test_homogeneo_infinitas_soluciones(self):
        # x + 2y = 0 ; 2x + 4y = 0  -> rango 1 < n, núcleo no trivial
        A = [[1.0, 2.0], [2.0, 4.0]]
        b = [0.0, 0.0]
        g, r, tags = resolver(A, b)

        self.assertTrue(g.is_homogeneous)
        self.assertEqual(r["status"], "infinite")
        self.assertEqual(r["dependencia"], "dependiente")
        self.assertIn("homogeneous_infinite", tags)

        # B3: la forma paramétrica tiene que existir de verdad, no ser None
        parametrica = r["parametric_solution"]
        self.assertIsNotNone(parametrica)
        self.assertIn("s1", parametrica)
        self.assertIn("parametric_solution", tags)

        # un vector no trivial del núcleo debe cumplir Ax = 0
        x = [-2.0, 1.0]
        for fila in A:
            self.assertAlmostEqual(sum(c * v for c, v in zip(fila, x)), 0.0, places=9)

    def test_no_homogeneo_infinitas_con_parametrica(self):
        # x + 2y + 3z = 6 ; 2x + 4y + 6z = 12  -> una ecuación útil, 2 libres
        A = [[1.0, 2.0, 3.0], [2.0, 4.0, 6.0]]
        b = [6.0, 12.0]
        g, r, tags = resolver(A, b)

        self.assertFalse(g.is_homogeneous)
        self.assertEqual(r["status"], "infinite")
        self.assertEqual(r["tipo_sistema"], "no homogéneo")
        self.assertIn("nonhom_infinite", tags)

        # Era el caso que B3 rompía: aquí la paramétrica no puede venir vacía
        parametrica = r["parametric_solution"]
        self.assertIsNotNone(parametrica)
        self.assertIn("s1", parametrica)
        self.assertIn("s2", parametrica)
        # las básicas siguen siendo x, el replace("x","s") las corrompía
        self.assertIn("x", parametrica)
        self.assertIn("parametric_solution", tags)

        # la solución particular (libres = 0) debe satisfacer el sistema
        x = r["solution"]
        for fila, termino in zip(A, b):
            self.assertAlmostEqual(sum(c * v for c, v in zip(fila, x)), termino, places=9)


class TestGaussJordanDependencia(unittest.TestCase):
    """Criterio de dependencia de filas: dependientes sii rank(A) < m."""

    def test_mas_filas_que_columnas_es_dependiente(self):
        # 3 vectores en R² son necesariamente dependientes.
        # El criterio viejo, rank < min(filas, n_vars), daba "independiente".
        A = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        b = [1.0, 1.0, 2.0]
        _, r, _ = resolver(A, b)
        self.assertEqual(r["dependencia"], "dependiente")

    def test_cuadrada_de_rango_completo_es_independiente(self):
        A = [[2.0, 1.0], [1.0, -1.0]]
        b = [5.0, 1.0]
        _, r, _ = resolver(A, b)
        self.assertEqual(r["dependencia"], "independiente")


class TestGaussJordanValidaciones(unittest.TestCase):
    """Validaciones de forma y tipo que aportó la rama Sistemas."""

    def test_filas_de_distinta_longitud(self):
        with self.assertRaises(ValueError):
            GaussJordanMethod([[1.0, 2.0], [3.0]], [1.0, 2.0])

    def test_matriz_vacia(self):
        with self.assertRaises(ValueError):
            GaussJordanMethod([], [])

    def test_elemento_no_numerico_en_A(self):
        with self.assertRaises(TypeError):
            GaussJordanMethod([[1.0, "x"], [3.0, 4.0]], [1.0, 2.0])

    def test_elemento_no_numerico_en_b(self):
        with self.assertRaises(TypeError):
            GaussJordanMethod([[1.0, 2.0], [3.0, 4.0]], [1.0, "y"])

    def test_homogeneity_check_es_el_primer_paso(self):
        # Se registra en run(), no en __init__: run() vacía el frame.
        g = GaussJordanMethod([[1.0, 2.0], [2.0, 4.0]], [0.0, 0.0])
        g.run()
        primer_tag = next(iter(g.frame.values()))["tag"]
        self.assertEqual(primer_tag, "homogeneity_check")


if __name__ == "__main__":
    unittest.main()
