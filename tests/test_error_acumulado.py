"""
Issue #8: error acumulado en interés compuesto.

Dos trayectorias desde el mismo monto inicial P, con tasa r por período:

    real:        I_k = r·R_{k-1}          R_k = R_{k-1} + I_k      (R_k = P(1+r)^k)
    aproximada:  Ĩ_k = q(r·A_{k-1})       A_k = A_{k-1} + Ĩ_k

q trunca (hacia cero) o redondea (mitad hacia arriba, lejos de cero) a
`approx_decimals` decimales. Por fila:

    difference_k = I_k - Ĩ_k                  (cuánto crece la brecha en la iteración)
    error_accum_k = R_k - A_k = Σ difference  (error total acumulado)
                  = (1+r)·E_{k-1} + δ_k,   δ_k = r·A_{k-1} - Ĩ_k  (error local)

Los valores esperados salen de `simular`, una implementación aparte con
fractions.Fraction y su propio truncado/redondeo, sin pasar por el motor.
"""
import json
import math
import os
import sys
import unittest
from decimal import Decimal
from fractions import Fraction

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

from rest_framework.test import APIClient

URL = '/api/v1/numeric/error-accumulation'


def q(x, d, modo):
    """Truncado hacia cero o redondeo mitad-arriba (lejos de cero), en Fraction."""
    f = Fraction(10) ** d
    y = x * f
    if modo == 'trunc':
        n = math.trunc(y)
    else:
        n = math.floor(abs(y) + Fraction(1, 2)) * (1 if y >= 0 else -1)
    return Fraction(n) / f


def simular(P, r, n, modo, d):
    R = A = Fraction(P)
    r = Fraction(r)
    filas = []
    for _ in range(n):
        I = R * r
        It = q(A * r, d, modo)
        local = A * r - It
        E_prev = R - A
        R2, A2 = R + I, A + It
        filas.append({'R_prev': R, 'A_prev': A, 'I': I, 'It': It, 'R': R2, 'A': A2,
                      'diff': I - It, 'E': R2 - A2, 'local': local, 'prop': r * E_prev})
        R, A = R2, A2
    return filas


def F(x):
    return Fraction(Decimal(x)) if isinstance(x, str) else Fraction(x)


class TestNucleo(unittest.TestCase):

    def setUp(self):
        from core.numeric.errores import calcular_error_acumulado
        self.calcular = calcular_error_acumulado

    def assertCoincideConSimulacion(self, P, r, n, modo, d):
        res = self.calcular(P, r, n, modo, d)
        esperado = simular(P, r, n, modo, d)
        self.assertEqual(len(res['filas']), n)
        for fila, e in zip(res['filas'], esperado):
            with self.subTest(iteracion=fila['iteracion']):
                self.assertEqual(F(fila['monto_anterior_real']), e['R_prev'])
                self.assertEqual(F(fila['monto_anterior_aprox']), e['A_prev'])
                self.assertEqual(F(fila['interes_real']), e['I'])
                self.assertEqual(F(fila['interes_aprox']), e['It'])
                self.assertEqual(F(fila['monto_real']), e['R'])
                self.assertEqual(F(fila['monto_aprox']), e['A'])
                self.assertEqual(F(fila['diferencia']), e['diff'])
                self.assertEqual(F(fila['error_acumulado']), e['E'])
                self.assertEqual(F(fila['error_local']), e['local'])
                self.assertEqual(F(fila['error_propagado']), e['prop'])
        return res

    def test_tabla_manual_truncado(self):
        # P = 1000, r = 5 %, truncar a 2 decimales (cálculo a mano):
        #   k  I real      Ĩ        R            A         diff      E
        #   1  50          50.00    1050         1050.00   0         0
        #   2  52.5        52.50    1102.5       1102.50   0         0
        #   3  55.125      55.12    1157.625     1157.62   0.005     0.005
        #   4  57.88125    57.88    1215.50625   1215.50   0.00125   0.00625
        res = self.assertCoincideConSimulacion('1000', '0.05', 4, 'trunc', 2)
        f = res['filas']
        self.assertEqual(f[2]['interes_aprox'], Decimal('55.12'))
        self.assertEqual(f[2]['error_acumulado'], Decimal('0.005'))
        self.assertEqual(f[3]['interes_real'], Decimal('57.88125'))
        self.assertEqual(f[3]['interes_aprox'], Decimal('57.88'))   # trunc(0.05·1157.62 = 57.881)
        self.assertEqual(f[3]['monto_real'], Decimal('1215.50625'))
        self.assertEqual(f[3]['monto_aprox'], Decimal('1215.50'))
        self.assertEqual(f[3]['diferencia'], Decimal('0.00125'))
        self.assertEqual(f[3]['error_acumulado'], Decimal('0.00625'))

    def test_tabla_manual_redondeo(self):
        # Mismo caso redondeando: 55.125 -> 55.13 (mitad hacia arriba): el
        # aproximado queda POR ENCIMA del real y el error es negativo.
        res = self.assertCoincideConSimulacion('1000', '0.05', 4, 'round', 2)
        f = res['filas']
        self.assertEqual(f[2]['interes_aprox'], Decimal('55.13'))
        self.assertEqual(f[2]['error_acumulado'], Decimal('-0.005'))
        self.assertEqual(f[3]['monto_aprox'], Decimal('1215.51'))
        self.assertEqual(f[3]['error_acumulado'], Decimal('-0.00375'))

    def test_trunc_y_round_difieren(self):
        t = self.calcular('1000', '0.05', 4, 'trunc', 2)['filas'][-1]
        r = self.calcular('1000', '0.05', 4, 'round', 2)['filas'][-1]
        self.assertNotEqual(t['monto_aprox'], r['monto_aprox'])
        self.assertNotEqual(t['error_acumulado'], r['error_acumulado'])
        self.assertEqual(t['monto_real'], r['monto_real'])  # la real no depende del modo

    def test_punto_medio(self):
        # I = 1000·0.00125 = 1.25 con 1 decimal: trunc 1.2, round 1.3.
        self.assertEqual(self.calcular('1000', '0.00125', 1, 'trunc', 1)['filas'][0]['interes_aprox'], Decimal('1.2'))
        self.assertEqual(self.calcular('1000', '0.00125', 1, 'round', 1)['filas'][0]['interes_aprox'], Decimal('1.3'))

    def test_acarreo_decimal(self):
        # I = 100·0.09995 = 9.995 con 2 decimales: round acarrea a 10.00.
        self.assertEqual(self.calcular('100', '0.09995', 1, 'round', 2)['filas'][0]['interes_aprox'], Decimal('10.00'))
        self.assertEqual(self.calcular('100', '0.09995', 1, 'trunc', 2)['filas'][0]['interes_aprox'], Decimal('9.99'))
        self.assertCoincideConSimulacion('100', '0.09995', 6, 'round', 2)

    def test_monto_negativo_trunca_hacia_cero(self):
        # I = -1.25: trunc hacia cero da -1.2 (no -1.3, que sería piso);
        # round mitad-arriba se aleja de cero: -1.3.
        self.assertEqual(self.calcular('-1000', '0.00125', 1, 'trunc', 1)['filas'][0]['interes_aprox'], Decimal('-1.2'))
        self.assertEqual(self.calcular('-1000', '0.00125', 1, 'round', 1)['filas'][0]['interes_aprox'], Decimal('-1.3'))
        self.assertCoincideConSimulacion('-1234.56', '0.037', 8, 'trunc', 2)

    def test_acumula_entre_iteraciones(self):
        res = self.calcular('1000', '0.0375', 10, 'trunc', 2)
        P, r = Fraction(1000), Fraction('0.0375')
        A_prev = P
        suma = Fraction(0)
        E_prev = Fraction(0)
        for k, fila in enumerate(res['filas'], start=1):
            # La real es P(1+r)^k exacto; la aproximada parte del A anterior,
            # no del monto inicial.
            self.assertEqual(F(fila['monto_real']), P * (1 + r) ** k)
            self.assertEqual(F(fila['interes_aprox']), q(A_prev * r, 2, 'trunc'))
            suma += F(fila['diferencia'])
            self.assertEqual(F(fila['error_acumulado']), suma)
            self.assertEqual(F(fila['error_acumulado']), (1 + r) * E_prev + F(fila['error_local']))
            A_prev, E_prev = F(fila['monto_aprox']), F(fila['error_acumulado'])
        self.assertGreater(res['filas'][-1]['error_acumulado'], 0)

    def test_tasa_cero(self):
        res = self.calcular('1000', '0', 3, 'trunc', 2)
        for fila in res['filas']:
            self.assertEqual(fila['monto_real'], 1000)
            self.assertEqual(fila['monto_aprox'], 1000)
            self.assertEqual(fila['error_acumulado'], 0)

    def test_caso_exacto_sin_error(self):
        # 1024 al 50 %: los intereses son enteros, sin nada que truncar.
        res = self.assertCoincideConSimulacion('1024', '0.5', 5, 'trunc', 0)
        for fila in res['filas']:
            self.assertEqual(fila['error_acumulado'], 0)
            self.assertEqual(fila['diferencia'], 0)

    def test_entradas_invalidas(self):
        casos = [
            ('', '0.05', 3, 'trunc', 2), ('NaN', '0.05', 3, 'trunc', 2), ('inf', '0.05', 3, 'trunc', 2),
            ('1e16', '0.05', 3, 'trunc', 2), ('1000.12345678901', '0.05', 3, 'trunc', 2),
            ('1000', '', 3, 'trunc', 2), ('1000', '-0.01', 3, 'trunc', 2), ('1000', '1.5', 3, 'trunc', 2),
            ('1000', '0.05', 0, 'trunc', 2), ('1000', '0.05', 51, 'trunc', 2),
            ('1000', '0.05', 3, 'floor', 2), ('1000', '0.05', 3, 'trunc', -1), ('1000', '0.05', 3, 'trunc', 11),
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                with self.assertRaises(ValueError):
                    self.calcular(*caso)


class TestEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = APIClient(raise_request_exception=False)

    def post(self, payload, status=200):
        r = self.client.post(URL, payload, format='json')
        self.assertEqual(r.status_code, status, getattr(r, 'data', None))
        return r.data

    BASE = {'initial_amount': '1000', 'iterations': 4, 'mode': 'trunc', 'rate': '0.05',
            'approx_decimals': 2, 'interest_display_decimals': 4}

    def test_contrato_del_frontend(self):
        data = self.post(self.BASE)
        self.assertEqual(data['input'], {
            'initial_amount': '1000', 'iterations': 4, 'mode': 'trunc', 'rate': '0.05',
            'approx_decimals': 2, 'interest_display_decimals': 4,
        })
        fila = data['data']['rows'][3]
        self.assertEqual(fila['iteration'], 4)
        self.assertEqual(fila['prev_amount_pretty'], '1157.62')          # A_3 (trayectoria aproximada)
        self.assertEqual(fila['prev_amount_approx_pretty'], '1157.62')
        self.assertEqual(fila['prev_amount_real_pretty'], '1157.6250')
        self.assertEqual(fila['interest_real_pretty'], '≈ 57.8813')      # 57.88125 con 4 decimales
        self.assertEqual(fila['interest_approx_pretty'], '57.88')
        self.assertEqual(fila['amount_real_pretty'], '≈ 1215.5063')
        self.assertEqual(fila['amount_approx_pretty'], '1215.50')
        self.assertEqual(fila['difference'], '0.00125')
        self.assertEqual(fila['difference_pretty'], '≈ 0.0013')
        self.assertEqual(fila['error_accum'], '0.00625')
        self.assertEqual(fila['error_accum_pretty'], '≈ 0.0063')
        self.assertEqual(fila['local_error'], '0.001')
        self.assertEqual(fila['propagated_error'], '0.00025')
        self.assertEqual(fila['amount_real'], '1215.50625')
        self.assertEqual(fila['approx_mode'], 'trunc')
        self.assertEqual(fila['approx_operation_text'], 'truncar a 2 decimales')

        s = data['data']['summary']
        self.assertEqual(s['iterations'], 4)
        self.assertEqual(s['initial_amount_pretty'], '1000')
        self.assertEqual(s['initial_amout_pretty'], s['initial_amount_pretty'])  # alias de compatibilidad
        self.assertEqual(s['final_error_accum'], '0.00625')
        self.assertEqual(s['final_error_accum_pretty'], '≈ 0.0063')
        self.assertEqual(s['final_amount_real_pretty'], '≈ 1215.5063')
        self.assertEqual(s['final_amount_approx_pretty'], '1215.50')
        self.assertEqual(s['rate'], '0.05')
        self.assertEqual(s['rate_percent'], '5 %')
        self.assertEqual(s['mode'], 'trunc')

    def test_ultima_fila_coincide_con_resumen(self):
        for modo in ('trunc', 'round'):
            with self.subTest(modo=modo):
                data = self.post({**self.BASE, 'mode': modo, 'iterations': 12, 'rate': '0.0375'})
                ultima, s = data['data']['rows'][-1], data['data']['summary']
                self.assertEqual(len(data['data']['rows']), s['iterations'])
                self.assertEqual(ultima['error_accum'], s['final_error_accum'])
                self.assertEqual(ultima['error_accum_pretty'], s['final_error_accum_pretty'])
                self.assertEqual(ultima['amount_real_pretty'], s['final_amount_real_pretty'])
                self.assertEqual(ultima['amount_approx_pretty'], s['final_amount_approx_pretty'])

    def test_contra_simulacion_independiente(self):
        for P, r, n, modo, d in [('1000', '0.05', 6, 'round', 2), ('2500.75', '0.0123', 10, 'trunc', 1),
                                 ('-1234.56', '0.037', 8, 'round', 2), ('100', '0.09995', 5, 'trunc', 2)]:
            with self.subTest(P=P, r=r, modo=modo):
                data = self.post({'initial_amount': P, 'iterations': n, 'mode': modo, 'rate': r, 'approx_decimals': d})
                for fila, e in zip(data['data']['rows'], simular(P, r, n, modo, d)):
                    self.assertEqual(F(fila['difference']), e['diff'])
                    self.assertEqual(F(fila['error_accum']), e['E'])
                    self.assertEqual(F(fila['amount_real']), e['R'])

    def test_decimales_de_presentacion_no_cambian_el_calculo(self):
        a = self.post({**self.BASE, 'interest_display_decimals': 1})
        b = self.post({**self.BASE, 'interest_display_decimals': 10})
        for fa, fb in zip(a['data']['rows'], b['data']['rows']):
            for clave in ('difference', 'error_accum', 'amount_real', 'amount_approx_pretty', 'interest_approx_pretty'):
                self.assertEqual(fa[clave], fb[clave], clave)
        self.assertEqual(b['data']['rows'][3]['amount_real_pretty'], '1215.5062500000')
        self.assertEqual(a['data']['rows'][3]['amount_real_pretty'], '≈ 1215.5')

    def test_presentacion_por_defecto_4_decimales(self):
        payload = dict(self.BASE)
        del payload['interest_display_decimals']
        data = self.post(payload)
        self.assertEqual(data['input']['interest_display_decimals'], 4)
        self.assertEqual(data['data']['rows'][2]['interest_real_pretty'], '55.1250')

    def test_tasa_cero_explicita_vs_vacia(self):
        data = self.post({**self.BASE, 'rate': '0'})
        self.assertEqual(data['data']['summary']['final_error_accum'], '0')
        self.assertEqual(data['data']['summary']['rate_percent'], '0 %')
        self.assertValidacion({**self.BASE, 'rate': ''}, 'rate')

    def test_sin_nan_ni_infinito(self):
        data = self.post({**self.BASE, 'iterations': 50, 'rate': '1', 'initial_amount': '1e15', 'approx_decimals': 0})
        texto = json.dumps(data, ensure_ascii=False)
        for malo in ('NaN', 'Infinity', 'inf'):
            self.assertNotIn(malo, texto)

    def assertValidacion(self, payload, campo):
        data = self.post(payload, status=400)
        self.assertEqual(data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn(campo, data['error']['message'])
        self.assertTrue(' '.join(map(str, data['error']['message'][campo])).strip())

    def test_entradas_invalidas_400(self):
        casos = [
            ('initial_amount', ''), ('initial_amount', 'abc'), ('initial_amount', 'NaN'),
            ('initial_amount', 'Infinity'), ('initial_amount', '1e16'),
            ('rate', 'NaN'), ('rate', '-0.05'), ('rate', '2'), ('rate', 'inf'),
            ('iterations', 0), ('iterations', 51), ('iterations', 2.5), ('iterations', 'abc'), ('iterations', None),
            ('mode', 'floor'), ('mode', ''),
            ('approx_decimals', -1), ('approx_decimals', 11), ('approx_decimals', 1.5),
            ('interest_display_decimals', -1), ('interest_display_decimals', 16),
        ]
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                self.assertValidacion({**self.BASE, campo: valor}, campo)

    def test_campos_obligatorios(self):
        for campo in ('initial_amount', 'iterations', 'mode', 'rate', 'approx_decimals'):
            with self.subTest(campo=campo):
                payload = dict(self.BASE)
                del payload[campo]
                self.assertValidacion(payload, campo)

    def test_mensajes_en_castellano(self):
        data = self.post({**self.BASE, 'initial_amount': ''}, status=400)
        self.assertIn('monto inicial', str(data['error']['message']['initial_amount']).lower())


if __name__ == '__main__':
    unittest.main()
