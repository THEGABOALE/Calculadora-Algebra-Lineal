"""
Fija, del lado del CLI, la corrección de "3.5/2" aplicada al consolidar
fraction_utils.py contra utils/EquationFunctions.py (ver commit
"refactor(web): deduplicar fraction_utils.py contra EquationFunctions.py").

La consolidación cambió parse_fraction para toda la web (ganó soporte para
numerador/denominador decimal), pero el CLI ya lo aceptaba desde antes, vía
la misma utils.EquationFunctions.parse_fraction: estos tests prueban que
consolidar no le quitó nada al CLI, no sólo que la web lo ganó.

Se mockea input() en vez de invocar la función suelta parse_fraction: así
se ejercita read_vector()/read_matrix_only(), las funciones reales que usan
los runners del CLI (cli/vector_runners.py, cli/matrix_runners.py,
cli/inputsmatrix.py), no sólo el parser en aislamiento.
"""
import unittest
from unittest.mock import patch

from core.vector_tools import read_vector
from cli.inputsmatrix import read_matrix_only


class TestCLIAceptaFraccionConNumeradorDecimal(unittest.TestCase):
    def test_read_vector_acepta_3_5_sobre_2(self):
        # Misma entrada que el test web equivalente: "3.5/2" = 1.75
        with patch('builtins.input', return_value='3.5/2 1'):
            v = read_vector(2)
        self.assertAlmostEqual(v.data[0], 1.75, places=9)
        self.assertAlmostEqual(v.data[1], 1.0, places=9)

    def test_read_matrix_only_acepta_3_5_sobre_2(self):
        with patch('builtins.input', return_value='3.5/2 0'):
            A = read_matrix_only(1, 2)
        self.assertAlmostEqual(A[0][0], 1.75, places=9)
        self.assertAlmostEqual(A[0][1], 0.0, places=9)


if __name__ == '__main__':
    unittest.main()
