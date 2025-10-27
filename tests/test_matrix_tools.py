import unittest
from utils import matrix_tools as mt

class TestMatrixTools(unittest.TestCase):

    def test_determinant_2x2(self):
        A = [[1.0, 2.0], [3.0, 4.0]]
        self.assertAlmostEqual(mt.determinant(A), -2.0)

    def test_inverse_2x2(self):
        A = [[4.0, 7.0], [2.0, 6.0]]
        Ainv, steps = mt.inverse(A)
        expected = [[0.6, -0.7], [-0.2, 0.4]]
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(Ainv[i][j], expected[i][j], places=9)

    def test_singular_matrix(self):
        A = [[1.0, 2.0], [2.0, 4.0]]  # filas dependientes
        det = mt.determinant(A)
        self.assertAlmostEqual(det, 0.0)
        with self.assertRaises(ValueError):
            mt.inverse(A)

    def test_determinant_3x3(self):
        A = [[1.0,2.0,3.0],[0.0,1.0,4.0],[5.0,6.0,0.0]]
        # Determinante conocido = 1
        self.assertAlmostEqual(mt.determinant(A), 1.0)

    def test_inverse_verify_ax_equals_b(self):
        A = [[4.0, 7.0], [2.0, 6.0]]
        b = [1.0, 1.0]
        Ainv, info = mt.inverse(A, b=b)
        # calcular x = Ainv * b
        x0 = Ainv[0][0]*b[0] + Ainv[0][1]*b[1]
        x1 = Ainv[1][0]*b[0] + Ainv[1][1]*b[1]
        # comprobar Ax = b
        Ax0 = A[0][0]*x0 + A[0][1]*x1
        Ax1 = A[1][0]*x0 + A[1][1]*x1
        self.assertAlmostEqual(Ax0, b[0], places=9)
        self.assertAlmostEqual(Ax1, b[1], places=9)

    def test_nullspace_nontrivial_and_verify(self):
        A = [[1.0, 2.0], [2.0, 4.0]]
        nullv = mt.nullspace_vector(A)
        self.assertIsNotNone(nullv)
        # comprobar Ax ≈ 0
        Ax0 = A[0][0]*nullv[0] + A[0][1]*nullv[1]
        Ax1 = A[1][0]*nullv[0] + A[1][1]*nullv[1]
        self.assertAlmostEqual(Ax0, 0.0, places=9)
        self.assertAlmostEqual(Ax1, 0.0, places=9)

    def test_verify_inverse_props_with_B(self):
        A = [[4.0,7.0],[2.0,6.0]]
        B = [[1.0,2.0],[3.0,4.0]]
        txt = mt.verify_inverse_props(A, B)
        # debe contener secciones a), b) y c)
        self.assertIn('a)', txt)
        self.assertIn('b)', txt)
        self.assertIn('c)', txt)

if __name__ == '__main__':
    unittest.main()
