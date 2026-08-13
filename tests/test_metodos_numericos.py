import math
import os
import subprocess
import sys
import unittest

from core.numeric.metodos_cerrados import metodo_biseccion, metodo_regla_falsa, verificar_intervalo
from core.numeric.metodos_abiertos import metodo_newton_raphson, metodo_secante


RAIZ_DE_2 = math.sqrt(2)

_RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LAC_DIR = os.path.join(_RAIZ_REPO, "linear_algebra_calculator")


class TestRaicesDeXCuadradoMenosDos(unittest.TestCase):
    """x**2 - 2 tiene raíz en sqrt(2); ambos métodos deben converger ahí."""

    def test_biseccion(self):
        resultado = metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-6)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)
        self.assertNotIn("advertencia", resultado)

    def test_newton_raphson_con_derivada_simbolica(self):
        # Antes este test se llamaba test_newton_raphson_con_derivada_numerica
        # y su comentario afirmaba que se usaba calcular_derivada_numerica
        # (diferencias centrales, h=1e-8). Esa función ya no existe: la
        # derivada se obtiene simbólicamente con sympy, que es exacta y no
        # arrastra error de truncamiento. Se renombra en vez de dejarlo pasar
        # en verde afirmando algo que dejó de ser cierto.
        resultado = metodo_newton_raphson("x**2 - 2", x0=1.5, tolerancia=1e-6)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)
        self.assertNotIn("advertencia", resultado)
        self.assertEqual(resultado["derivada_latex"], "2 x")


class TestHistorialRegistraLosDosExtremos(unittest.TestCase):
    """Bisección calculaba f(a) para decidir el subintervalo y lo descartaba;
    f(b) ni se calculaba. Un adaptador que quiera mostrar ambas ramas de la
    tabla (yl, yu) no tiene de dónde sacarlas si el motor no las registra.
    Mismo caso en la secante con f(x_{n+1}): se calcula recién al arrancar la
    iteración siguiente, así que la última fila del historial nunca la tuvo."""

    def test_biseccion_registra_f_de_a_y_f_de_b(self):
        resultado = metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-6)
        for fila in resultado["historial"]:
            self.assertIn("f(a)", fila)
            self.assertIn("f(b)", fila)
            # f(a) y f(b) deben corresponder de verdad a los extremos de esa
            # fila, no a un valor arrastrado de otra iteración.
            self.assertAlmostEqual(fila["f(a)"], fila["a"] ** 2 - 2, places=9)
            self.assertAlmostEqual(fila["f(b)"], fila["b"] ** 2 - 2, places=9)

    def test_biseccion_no_cambia_de_raiz_al_agregar_los_campos(self):
        # Los campos nuevos son aditivos: evaluar f(b) no debe alterar qué
        # subintervalo se elige ni a qué raíz converge.
        resultado = metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-8)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)

    def test_secante_registra_f_de_x_siguiente(self):
        resultado = metodo_secante("x**2 - 2", 1.0, 2.0, tolerancia=1e-6)
        for fila in resultado["historial"]:
            self.assertIn("f(x_{n+1})", fila)
            self.assertAlmostEqual(
                fila["f(x_{n+1})"], fila["x_{n+1}"] ** 2 - 2, places=9
            )

    def test_secante_no_cambia_de_raiz_al_agregar_el_campo(self):
        resultado = metodo_secante("x**2 - 2", 1.0, 2.0, tolerancia=1e-8)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)


class TestVerificarIntervalo(unittest.TestCase):
    def test_rechaza_intervalo_sin_cambio_de_signo(self):
        # x**2 - 2 es positiva en todo [2, 3]: no hay cambio de signo.
        self.assertFalse(verificar_intervalo("x**2 - 2", 2.0, 3.0))

    def test_acepta_intervalo_con_cambio_de_signo(self):
        self.assertTrue(verificar_intervalo("x**2 - 2", 1.0, 2.0))

    def test_biseccion_rechaza_intervalo_invalido(self):
        # Es el test que prueba que el chequeo de Bolzano vive en el motor y
        # no en la capa que llama: sin él, el CLI aceptaría un intervalo sin
        # cambio de signo y devolvería una raíz falsa.
        with self.assertRaises(ValueError):
            metodo_biseccion("x**2 - 2", 2.0, 3.0, tolerancia=1e-6)


class TestSympyNoSeCargaAlArrancar(unittest.TestCase):
    """sympy (y, desde la Fase 5, antlr4) se importan dentro de las funciones
    que los necesitan, nunca a nivel de módulo.

    cli/startup.py importa cli.numerical_methods_runners a nivel de módulo, y
    ese runner importa core.numeric.* también a nivel de módulo: si sympy se
    cargara arriba, el CLI entero lo pagaría en cada arranque, antes de
    mostrar el menú, aunque el usuario sólo vaya a resolver una matriz. Es el
    mismo problema que utils/symbolic_equations.py documenta para symengine,
    que se cargaba en cada arranque de la web.

    antlr4-python3-runtime (Fase 5, api/adapters/latex.py, para
    sympy.parsing.latex.parse_latex) es todavía más pesada que sympy y más
    fácil de arrastrar sin querer -- está confinada al adaptador de LaTeX de
    la API, y cli/startup.py no debería cargarla nunca: el CLI escribe
    funciones en texto plano ("x**2 - 2"), no LaTeX.

    Se corre en un subproceso limpio a propósito: dentro de esta misma suite
    otros tests ya importaron sympy al llamar a los métodos, así que mirar
    sys.modules acá adentro daría un falso negativo.
    """

    def _modulos_cargados_tras(self, codigo: str, *modulos: str) -> dict:
        entorno = dict(os.environ, PYTHONPATH=_LAC_DIR, PYTHONIOENCODING="utf-8")
        chequeos = "\n".join(f"print({m!r} in sys.modules)" for m in modulos)
        completo = f"{codigo}\nimport sys\n{chequeos}\n"
        salida = subprocess.run(
            [sys.executable, "-c", completo],
            capture_output=True, text=True, cwd=_RAIZ_REPO, env=entorno,
        )
        self.assertEqual(salida.returncode, 0, f"el subproceso falló:\n{salida.stderr}")
        lineas = salida.stdout.strip().splitlines()[-len(modulos):]
        return dict(zip(modulos, (linea == "True" for linea in lineas)))

    def _sympy_cargado_tras(self, codigo: str) -> bool:
        return self._modulos_cargados_tras(codigo, "sympy")["sympy"]

    def test_importar_cli_startup_no_carga_sympy(self):
        self.assertFalse(self._sympy_cargado_tras("import cli.startup"))

    def test_importar_cli_startup_no_carga_antlr4_ni_rest_framework(self):
        # cli/startup.py no toca Django (nunca llama django.setup()), así que
        # a diferencia de calculator.views, acá ni siquiera rest_framework
        # tendría motivo para cargarse -- es el chequeo más estricto posible.
        cargados = self._modulos_cargados_tras(
            "import cli.startup", "antlr4", "rest_framework"
        )
        self.assertFalse(cargados["antlr4"])
        self.assertFalse(cargados["rest_framework"])

    def test_importar_calculator_views_no_carga_sympy(self):
        codigo = (
            "import os, django\n"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linear_algebra_calculator.settings')\n"
            "django.setup()\n"
            "import calculator.views"
        )
        self.assertFalse(self._sympy_cargado_tras(codigo))

    def test_importar_calculator_views_no_carga_antlr4(self):
        # rest_framework SÍ se carga acá -- django.setup() importa todas las
        # apps de INSTALLED_APPS, incluida 'rest_framework', sin importar qué
        # vista se use. Eso no es el problema: antlr4 es la dependencia
        # pesada que sólo debería tocar api/adapters/latex.py, y calculator/
        # (la web de templates, ajena a la API) no tiene motivo para cargarla.
        codigo = (
            "import os, django\n"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linear_algebra_calculator.settings')\n"
            "django.setup()\n"
            "import calculator.views"
        )
        cargados = self._modulos_cargados_tras(codigo, "antlr4", "rest_framework")
        self.assertFalse(cargados["antlr4"])
        self.assertTrue(cargados["rest_framework"])

    def test_importar_los_metodos_tampoco_lo_carga_hasta_usarlos(self):
        # Importar el módulo no debe bastar; recién al resolver aparece sympy.
        self.assertFalse(
            self._sympy_cargado_tras("import core.numeric.metodos_cerrados")
        )
        self.assertTrue(
            self._sympy_cargado_tras(
                "from core.numeric.metodos_cerrados import metodo_biseccion\n"
                "metodo_biseccion('x**2 - 2', 1.0, 2.0, tolerancia=1e-6)"
            )
        )

    def test_importar_adapters_latex_no_carga_antlr4_hasta_usarlo(self):
        entorno_api = (
            "import os, django\n"
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linear_algebra_calculator.settings')\n"
            "django.setup()\n"
        )
        self.assertFalse(
            self._modulos_cargados_tras(
                entorno_api + "import api.adapters.latex", "antlr4"
            )["antlr4"]
        )
        self.assertTrue(
            self._modulos_cargados_tras(
                entorno_api
                + "from api.adapters.latex import latex_a_texto\n"
                + "latex_a_texto('x^2 - 2')",
                "antlr4",
            )["antlr4"]
        )


# Las cuatro funciones que el propio CLI ofrece como ejemplo al pedir f(x).
FUNCIONES_DE_EJEMPLO = (
    "x**2 - 4",
    "x**3 - 2*x - 5",
    "exp(x) - 3*x",
    "sin(x) - x/2",
)


def _evaluar_con_eval(f_str, x):
    """Reimplementación literal del evaluar_funcion que había antes.

    Se conserva acá, en el test y no en el código, como referencia contra la
    cual medir que el cambio de eval() a sympy no alteró resultados.
    """
    import math
    seguro = {
        'x': x, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'exp': math.exp, 'log': math.log, 'log10': math.log10,
        'sqrt': math.sqrt, 'abs': abs, 'pi': math.pi, 'e': math.e,
    }
    return float(eval(f_str.replace('^', '**'), {"__builtins__": {}}, seguro))


class TestEquivalenciaDeNotacion(unittest.TestCase):
    """`^` es potencia para quien escribe la función, pero en sympy (como en
    Python) es XOR binario: sin traducirlo, `x^2` se parsearía como
    `Xor(x, 2)` sin error y con un resultado silenciosamente incorrecto. El
    eval() anterior hacía el reemplazo `^` -> `**` y hay que conservarlo."""

    def test_circunflejo_equivale_a_doble_asterisco(self):
        from core.numeric._expresiones import compilar, evaluar

        for con_potencia, con_circunflejo in (
            ("x**2 - 4", "x^2 - 4"),
            ("x**3 - 2*x - 5", "x^3 - 2*x - 5"),
            ("x**2 + x**3", "x^2 + x^3"),
        ):
            f_a, expr_a, _ = compilar(con_potencia)
            f_b, expr_b, _ = compilar(con_circunflejo)
            self.assertEqual(expr_a, expr_b, f"{con_potencia} vs {con_circunflejo}")
            for x in (-2.0, -0.5, 0.0, 1.5, 3.0):
                self.assertAlmostEqual(
                    evaluar(f_a, x), evaluar(f_b, x), places=12,
                    msg=f"{con_potencia} vs {con_circunflejo} en x={x}",
                )

    def test_circunflejo_no_queda_como_xor(self):
        from core.numeric._expresiones import compilar, evaluar

        # Con XOR, x^2 en x=3 daria 1 (3 xor 2). Como potencia, 9.
        f, _, _ = compilar("x^2")
        self.assertAlmostEqual(evaluar(f, 3.0), 9.0, places=12)

    def test_sympy_coincide_con_el_eval_anterior(self):
        from core.numeric._expresiones import compilar, evaluar

        for f_str in FUNCIONES_DE_EJEMPLO:
            f, _, _ = compilar(f_str)
            for x in (-1.5, -0.25, 0.0, 0.5, 1.0, 2.0, 3.5):
                self.assertAlmostEqual(
                    evaluar(f, x), _evaluar_con_eval(f_str, x), places=10,
                    msg=f"f(x) = {f_str} en x = {x}",
                )

    def test_las_funciones_de_ejemplo_del_cli_parsean(self):
        from core.numeric._expresiones import compilar

        for f_str in FUNCIONES_DE_EJEMPLO:
            with self.subTest(f_str=f_str):
                compilar(f_str)

    def test_funcion_invalida_da_valueerror(self):
        from core.numeric._expresiones import compilar

        for basura in ("x +* 2", "sen(x)", "y**2 - 1", ""):
            with self.subTest(basura=basura):
                with self.assertRaises(ValueError):
                    compilar(basura)


class TestLosCuatroMetodosConvergenALaMismaRaiz(unittest.TestCase):
    """Comparación cruzada que hoy no existía: los cuatro métodos, sobre la
    misma función, deben coincidir en la raíz que encuentran."""

    def test_x_cuadrado_menos_dos(self):
        raices = {
            "biseccion": metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-8)["raiz"],
            "regla_falsa": metodo_regla_falsa("x**2 - 2", 1.0, 2.0, tolerancia=1e-8)["raiz"],
            "newton": metodo_newton_raphson("x**2 - 2", x0=1.5, tolerancia=1e-8)["raiz"],
            "secante": metodo_secante("x**2 - 2", 1.0, 2.0, tolerancia=1e-8)["raiz"],
        }
        for nombre, raiz in raices.items():
            with self.subTest(metodo=nombre):
                self.assertAlmostEqual(raiz, RAIZ_DE_2, places=6)

    def test_x_cubo_menos_dos_x_menos_cinco(self):
        # Raíz conocida ~ 2.0945514815423265 (única raíz real).
        f_str = "x**3 - 2*x - 5"
        raiz_conocida = 2.0945514815423265
        raices = {
            "biseccion": metodo_biseccion(f_str, 2.0, 3.0, tolerancia=1e-8)["raiz"],
            "regla_falsa": metodo_regla_falsa(f_str, 2.0, 3.0, tolerancia=1e-8)["raiz"],
            "newton": metodo_newton_raphson(f_str, x0=2.0, tolerancia=1e-8)["raiz"],
            "secante": metodo_secante(f_str, 2.0, 3.0, tolerancia=1e-8)["raiz"],
        }
        for nombre, raiz in raices.items():
            with self.subTest(metodo=nombre):
                self.assertAlmostEqual(raiz, raiz_conocida, places=6)


class TestCriterioIntervalo(unittest.TestCase):
    """criterio="intervalo" corta por longitud de intervalo, no por error
    relativo, y trae su propia estimación de iteraciones por log2."""

    def test_converge_a_la_misma_raiz_que_error_relativo(self):
        r_intervalo = metodo_biseccion(
            "x**2 - 2", 1.0, 2.0, tolerancia=1e-8, criterio="intervalo"
        )
        self.assertAlmostEqual(r_intervalo["raiz"], RAIZ_DE_2, places=6)
        self.assertEqual(r_intervalo["criterio"], "intervalo")

    def test_estimacion_de_iteraciones_coincide_con_log2(self):
        a, b, tol = 1.0, 2.0, 1e-8
        resultado = metodo_biseccion("x**2 - 2", a, b, tolerancia=tol, criterio="intervalo")
        estimacion = resultado["estimacion_iteraciones"]

        esperado = math.log2((b - a) / tol)
        self.assertAlmostEqual(estimacion["estimado"], esperado, places=9)
        self.assertEqual(estimacion["n_minimo"], math.ceil(esperado))

    def test_error_relativo_no_trae_estimacion_de_iteraciones(self):
        resultado = metodo_biseccion(
            "x**2 - 2", 1.0, 2.0, tolerancia=1e-8, criterio="error_relativo"
        )
        self.assertNotIn("estimacion_iteraciones", resultado)

    def test_criterio_desconocido_da_valueerror(self):
        with self.assertRaises(ValueError):
            metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-6, criterio="otra_cosa")

    def test_regla_falsa_tambien_soporta_criterio_intervalo(self):
        resultado = metodo_regla_falsa(
            "x**2 - 2", 1.0, 2.0, tolerancia=1e-8, criterio="intervalo"
        )
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)
        self.assertIn("estimacion_iteraciones", resultado)


class TestDegeneraciones(unittest.TestCase):
    """Condiciones donde la fórmula del método no está definida: deben
    levantar excepción, no devolver una raíz aproximada con 'advertencia'."""

    def test_newton_con_derivada_identicamente_nula(self):
        # f(x) = 5 es constante: f'(x) = 0 en todo punto.
        with self.assertRaises(ValueError):
            metodo_newton_raphson("5", x0=1.0, tolerancia=1e-6)

    def test_newton_con_derivada_nula_en_una_iteracion(self):
        # f(x) = x**3 - 2x + 2 tiene f'(x) = 3x**2 - 2, que se anula en
        # x = sqrt(2/3). Arrancar justo ahí fuerza f'(x0) = 0 en la primera
        # iteración sin que la derivada sea idénticamente nula.
        x0 = math.sqrt(2.0 / 3.0)
        with self.assertRaises(ZeroDivisionError):
            metodo_newton_raphson("x**3 - 2*x + 2", x0=x0, tolerancia=1e-6)

    def test_secante_con_denominador_nulo(self):
        # f(x) = x**2 - 2 evaluada en x0=-x1 da el mismo valor en ambos
        # puntos: f(x_n) - f(x_{n-1}) = 0 en la primera iteración.
        with self.assertRaises(ZeroDivisionError):
            metodo_secante("x**2 - 2", -1.5, 1.5, tolerancia=1e-6)

    def test_regla_falsa_rechaza_intervalo_sin_cambio_de_signo(self):
        # Igual que bisección: hereda la misma validación de Bolzano.
        with self.assertRaises(ValueError):
            metodo_regla_falsa("x**2 - 2", 2.0, 3.0, tolerancia=1e-6)

    def test_regla_falsa_acepta_intervalo_valido(self):
        resultado = metodo_regla_falsa("x**2 - 2", 1.0, 2.0, tolerancia=1e-8)
        self.assertAlmostEqual(resultado["raiz"], RAIZ_DE_2, places=6)
        self.assertNotIn("advertencia", resultado)

    def test_no_convergencia_deja_advertencia_no_excepcion(self):
        # max_iter=1 no alcanza para que el error relativo baje de la
        # tolerancia (se necesita al menos 2 iteraciones para calcularlo).
        resultado = metodo_biseccion("x**2 - 2", 1.0, 2.0, tolerancia=1e-12, max_iter=1)
        self.assertIn("advertencia", resultado)
        self.assertEqual(resultado["iteraciones"], 1)


if __name__ == "__main__":
    unittest.main()
