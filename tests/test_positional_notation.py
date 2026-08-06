import unittest

from core.positional_notation import decompose_base10_decimal, decompose_base2_str


class TestIdaYVuelta(unittest.TestCase):
    """decimal -> base 2 -> decimal debe devolver el número original."""

    def test_13_ida_y_vuelta(self):
        original = 13

        binario = decompose_base2_str(bin(original)[2:])
        self.assertEqual(binario["decimal_equiv"], original)

        decimal = decompose_base10_decimal(binario["decimal_equiv"])
        self.assertEqual(decimal["int_part"], original)
        self.assertAlmostEqual(decimal["total"], original, places=9)

    def test_255_ida_y_vuelta(self):
        original = 255  # 11111111, ejercita más términos que 13

        binario = decompose_base2_str(bin(original)[2:])
        self.assertEqual(binario["decimal_equiv"], original)
        self.assertEqual(len(binario["bits"]), 8)

        decimal = decompose_base10_decimal(binario["decimal_equiv"])
        self.assertEqual(decimal["int_part"], original)
        self.assertAlmostEqual(decimal["total"], original, places=9)


class TestDecompose(unittest.TestCase):
    def test_base10_con_decimales(self):
        # 13.5 = 1x10^1 + 3x10^0 + 5x10^-1
        d = decompose_base10_decimal("13.5")
        self.assertAlmostEqual(d["total"], 13.5, places=9)
        self.assertEqual(d["int_part"], 13)
        self.assertAlmostEqual(d["frac_part"], 0.5, places=9)

    def test_base2_string_invalida(self):
        with self.assertRaises(ValueError):
            decompose_base2_str("102")


if __name__ == "__main__":
    unittest.main()
