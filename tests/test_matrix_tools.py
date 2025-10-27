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

if __name__ == '__main__':
    unittest.main()
