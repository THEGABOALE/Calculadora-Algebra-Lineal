"""
Tests de las rutas web añadidas en la Fase 7: vectores, operaciones de
matrices, y los dos métodos nuevos (combinacion_lineal, ax) sobre la ruta
existente de sistemas de ecuaciones.

Usa django.test.Client directamente (no django.test.TestCase): la app no
guarda nada en base de datos en estas vistas, así que no hace falta la
maquinaria de transacciones/DB de prueba de Django, que exige correr con
manage.py test. Esto se integra con el runner del proyecto,
python -m unittest discover tests, igual que el resto de la suite.

Nota de sys.path: al correr `python -m unittest discover tests` desde la
raíz del repo, Python añade '' (cwd = raíz) a sys.path, y ese '' queda antes
que linear_algebra_calculator/ (agregado vía PYTHONPATH). La raíz del repo
tiene su propio calculator/ -- el stub de app Django vacío mencionado desde
la Fase 1, sin urls.py -- así que `import calculator` resolvía ahí primero
y Django reventaba con "No module named 'calculator.urls'". Se antepone
linear_algebra_calculator/ explícitamente antes de que Django resuelva
cualquier URL. No se toca el stub en sí: limpiarlo es Fase 8.
"""
import os
import sys
import unittest

_LAC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'linear_algebra_calculator')
sys.path.insert(0, _LAC_DIR)

import django
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linear_algebra_calculator.settings')
if not apps.ready:
    django.setup()

from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

from django.test import Client


class TestVectorInput(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_muestra_el_formulario_de_dimension(self):
        r = self.client.get('/vectorInput/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Dimensión', r.content.decode('utf-8'))

    def test_post_dimension_muestra_formulario_de_vectores(self):
        r = self.client.post('/vectorInput/', {'n': '2'})
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertIn('Vector v', html)
        self.assertIn('Vector w', html)


class TestVectorResolution(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_suma(self):
        # v=(2,3) w=(1,1) -> v+w=(3,4)
        r = self.client.post('/vectorResolution/', {
            'n': '2', 'method': 'suma', 'v_0': '2', 'v_1': '3', 'w_0': '1', 'w_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('3, 4', r.content.decode('utf-8'))

    def test_resta(self):
        # v=(2,3) w=(1,1) -> v-w=(1,2)
        r = self.client.post('/vectorResolution/', {
            'n': '2', 'method': 'resta', 'v_0': '2', 'v_1': '3', 'w_0': '1', 'w_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('1, 2', r.content.decode('utf-8'))

    def test_producto_punto(self):
        # v=(2,3) w=(1,1) -> v.w = 2*1+3*1 = 5
        r = self.client.post('/vectorResolution/', {
            'n': '2', 'method': 'producto_punto', 'v_0': '2', 'v_1': '3', 'w_0': '1', 'w_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('Resultado:</b> 5', r.content.decode('utf-8'))

    def test_acepta_fraccion_con_numerador_decimal(self):
        # Fija la corrección de la consolidación fraction_utils -> EquationFunctions:
        # "3.5/2" (numerador decimal) se rechazaba en la web antes de esa consolidación.
        # parse_fraction("3.5/2") = 1.75; v=(1.75, 1) w=(1, 1) -> v+w=(2.75, 2) = (11/4, 2)
        r = self.client.post('/vectorResolution/', {
            'n': '2', 'method': 'suma', 'v_0': '3.5/2', 'v_1': '1', 'w_0': '1', 'w_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertNotIn('Error en la entrada', html)
        self.assertIn('11/4, 2', html)

    def test_rechaza_campos_vacios(self):
        r = self.client.post('/vectorResolution/', {
            'n': '2', 'method': 'suma', 'v_0': '', 'v_1': '3', 'w_0': '1', 'w_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('deben estar llenos', r.content.decode('utf-8'))


class TestMatrixInput(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_muestra_formulario_de_dimensiones(self):
        r = self.client.get('/matrixInput/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('dimensiones de la matriz', r.content.decode('utf-8'))

    def test_post_dimensiones_muestra_formulario_de_matriz(self):
        r = self.client.post('/matrixInput/', {'rows': '2', 'cols': '2'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Matriz A', r.content.decode('utf-8'))


class TestMatrixOperationResolution(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_determinante(self):
        # det([[1,2],[3,4]]) = 1*4 - 2*3 = -2
        r = self.client.post('/matrixOperationResolution/', {
            'rows': '2', 'cols': '2', 'method': 'determinante',
            'matrix_0_0': '1', 'matrix_0_1': '2', 'matrix_1_0': '3', 'matrix_1_1': '4',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('Resultado:</b> -2', r.content.decode('utf-8'))

    def test_acepta_fraccion_con_numerador_decimal(self):
        # Misma corrección que en TestVectorResolution, ahora sobre una celda de
        # la matriz: det([[1.75, 0], [0, 1]]) = 1.75 = 7/4.
        r = self.client.post('/matrixOperationResolution/', {
            'rows': '2', 'cols': '2', 'method': 'determinante',
            'matrix_0_0': '3.5/2', 'matrix_0_1': '0', 'matrix_1_0': '0', 'matrix_1_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertNotIn('Error en la entrada', html)
        self.assertIn('Resultado:</b> 7/4', html)

    def test_inversa(self):
        # A=[[4,7],[2,6]] -> A^-1 = [[3/5,-7/10],[-1/5,2/5]] = [[0.6,-0.7],[-0.2,0.4]]
        r = self.client.post('/matrixOperationResolution/', {
            'rows': '2', 'cols': '2', 'method': 'inversa',
            'matrix_0_0': '4', 'matrix_0_1': '7', 'matrix_1_0': '2', 'matrix_1_1': '6',
        })
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertIn('3/5', html)
        self.assertIn('-7/10', html)
        self.assertIn('-1/5', html)
        self.assertIn('2/5', html)

    def test_rango_matriz_singular(self):
        # [[1,2],[2,4]]: filas dependientes, rango 1
        r = self.client.post('/matrixOperationResolution/', {
            'rows': '2', 'cols': '2', 'method': 'rango',
            'matrix_0_0': '1', 'matrix_0_1': '2', 'matrix_1_0': '2', 'matrix_1_1': '4',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('rango(A) = 1', r.content.decode('utf-8'))

    def test_transpuesta(self):
        # [[1,2,3],[4,5,6]]^T -> filas [1,4] [2,5] [3,6]
        r = self.client.post('/matrixOperationResolution/', {
            'rows': '2', 'cols': '3', 'method': 'transpuesta',
            'matrix_0_0': '1', 'matrix_0_1': '2', 'matrix_0_2': '3',
            'matrix_1_0': '4', 'matrix_1_1': '5', 'matrix_1_2': '6',
        })
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertIn(
            "<tr><td>1</td><td>4</td></tr><tr><td>2</td><td>5</td></tr><tr><td>3</td><td>6</td></tr>",
            html,
        )

    def test_determinante_rechaza_matriz_no_cuadrada(self):
        r = self.client.post('/matrixOperationResolution/', {
            'rows': '2', 'cols': '3', 'method': 'determinante',
            'matrix_0_0': '1', 'matrix_0_1': '2', 'matrix_0_2': '3',
            'matrix_1_0': '4', 'matrix_1_1': '5', 'matrix_1_2': '6',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('cuadradas', r.content.decode('utf-8'))


class TestEcuationResolutionNuevosMetodos(unittest.TestCase):
    """combinacion_lineal y ax se agregaron como métodos nuevos sobre la
    ruta /ecuationResolution/ ya existente, no sobre una ruta propia."""

    def setUp(self):
        self.client = Client()

    def test_combinacion_lineal_unica(self):
        # v1=(1,0) v2=(0,1) b=(3,4) -> A=I, unica solucion x=(3,4)
        r = self.client.post('/ecuationResolution/', {
            'rows': '2', 'cols': '2', 'method': 'combinacion_lineal',
            'matrix_0_0': '1', 'matrix_0_1': '0', 'matrix_1_0': '0', 'matrix_1_1': '1',
            'vector_0': '3', 'vector_1': '4',
        })
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertIn('ÚNICA', html)
        self.assertIn('combinación lineal', html)

    def test_ax_producto(self):
        # A=I, x=(5,7) -> Ax=(5,7)
        r = self.client.post('/ecuationResolution/', {
            'rows': '2', 'cols': '2', 'method': 'ax',
            'matrix_0_0': '1', 'matrix_0_1': '0', 'matrix_1_0': '0', 'matrix_1_1': '1',
            'vector_0': '5', 'vector_1': '7',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('A·x = [5, 7]', r.content.decode('utf-8'))

    def test_ax_rechaza_dimension_incompatible(self):
        # A es 2x3 pero el campo vector sólo aporta 2 valores (=filas), no 3 (=columnas)
        r = self.client.post('/ecuationResolution/', {
            'rows': '2', 'cols': '3', 'method': 'ax',
            'matrix_0_0': '1', 'matrix_0_1': '2', 'matrix_0_2': '3',
            'matrix_1_0': '4', 'matrix_1_1': '5', 'matrix_1_2': '6',
            'vector_0': '1', 'vector_1': '1',
        })
        self.assertEqual(r.status_code, 200)
        self.assertIn('Dimensiones incompatibles', r.content.decode('utf-8'))


class TestNavegacion(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_calculator_main_enlaza_a_las_rutas_nuevas(self):
        r = self.client.get('/calculatorMain/')
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertIn('/vectorInput/', html)
        self.assertIn('/matrixInput/', html)


if __name__ == '__main__':
    unittest.main()
