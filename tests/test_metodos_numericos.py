import math
import unittest

from core.numeric.metodos_cerrados import metodo_biseccion, verificar_intervalo
from core.numeric.metodos_abiertos import metodo_newton_raphson


RAIZ_DE_2 = math.sqrt(2)


class TestRaicesDeXCuadradoMenosDos(unittest.TestCase):
    """x**2 - 2 tiene raíz en sqrt(2); ambos métodos deben converger ahí."""

    def test_biseccion(self):
        resultado = metodo_biseccion("x**2 - 2", 1.0, 2.0, error_deseado=1e-6)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)
        self.assertNotIn("advertencia", resultado)

    def test_newton_raphson_con_derivada_numerica(self):
        # derivada_str=None -> usa calcular_derivada_numerica (diferencias
        # centrales, h=1e-8), no una derivada analítica provista a mano.
        resultado = metodo_newton_raphson("x**2 - 2", x0=1.5, error_deseado=1e-6)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)
        self.assertNotIn("advertencia", resultado)


class TestVerificarIntervalo(unittest.TestCase):
    def test_rechaza_intervalo_sin_cambio_de_signo(self):
        # x**2 - 2 es positiva en todo [2, 3]: no hay cambio de signo.
        self.assertFalse(verificar_intervalo("x**2 - 2", 2.0, 3.0))

    def test_acepta_intervalo_con_cambio_de_signo(self):
        self.assertTrue(verificar_intervalo("x**2 - 2", 1.0, 2.0))

    def test_biseccion_rechaza_intervalo_invalido(self):
        with self.assertRaises(ValueError):
            metodo_biseccion("x**2 - 2", 2.0, 3.0, error_deseado=1e-6)


if __name__ == "__main__":
    unittest.main()
