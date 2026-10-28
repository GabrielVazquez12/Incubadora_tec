import unittest
from decimal import Decimal

from app.modules.incubadora.workflow import DEFAULT_ROUTES, _project_steps, calculate
from app.schemas.ruta_emprendedora import CalculadoraInput


class EconomicRouteRulesTest(unittest.TestCase):
    def calculate(self, **values):
        values.setdefault('observaciones', '')
        return calculate(CalculadoraInput(**values), Decimal('10'), 36)

    def test_calculates_monthly_results_and_green_threshold(self):
        result = self.calculate(
            inversion_inicial=10000, costos_fijos=1000, costo_variable_unitario=30,
            precio_venta=100, unidades_estimadas=100,
        )
        self.assertEqual(result['ingreso_mensual'], 10000)
        self.assertEqual(result['costo_variable_mensual'], 3000)
        self.assertEqual(result['costo_total_mensual'], 4000)
        self.assertEqual(result['utilidad_mensual'], 6000)
        self.assertEqual(result['punto_equilibrio_unidades'], 14.29)
        self.assertEqual(result['unidades_equilibrio_redondeadas'], 15)
        self.assertEqual(result['margen_porcentaje'], 60)
        self.assertEqual(result['meses_recuperacion'], 1.67)
        self.assertEqual(result['semaforo'], 'verde')

    def test_red_if_price_does_not_cover_variable_cost_or_profit_is_zero(self):
        result = self.calculate(
            inversion_inicial=0, costos_fijos=0, costo_variable_unitario=10,
            precio_venta=10, unidades_estimadas=100,
        )
        self.assertEqual(result['semaforo'], 'rojo')
        self.assertIsNone(result['punto_equilibrio_unidades'])
        self.assertEqual(result['margen_porcentaje'], 0)
        self.assertEqual(result['causas'], [
            'El precio no cubre el costo variable unitario.',
            'La utilidad mensual estimada no es positiva.',
        ])

    def test_yellow_for_weak_margin_or_long_recovery(self):
        weak_margin = self.calculate(
            inversion_inicial=100000, costos_fijos=0, costo_variable_unitario=95,
            precio_venta=100, unidades_estimadas=1000,
        )
        self.assertEqual(weak_margin['margen_porcentaje'], 5)
        self.assertEqual(weak_margin['semaforo'], 'amarillo')
        long_recovery = self.calculate(
            inversion_inicial=500000, costos_fijos=0, costo_variable_unitario=50,
            precio_venta=100, unidades_estimadas=100,
        )
        self.assertEqual(long_recovery['meses_recuperacion'], 100)
        self.assertEqual(long_recovery['semaforo'], 'amarillo')

    def test_red_below_break_even_and_zero_investment_does_not_need_payback(self):
        below = self.calculate(
            inversion_inicial=1000, costos_fijos=7000, costo_variable_unitario=30,
            precio_venta=100, unidades_estimadas=50,
        )
        self.assertEqual(below['semaforo'], 'rojo')
        zero_initial = self.calculate(
            inversion_inicial=0, costos_fijos=100, costo_variable_unitario=30,
            precio_venta=100, unidades_estimadas=10,
        )
        self.assertEqual(zero_initial['meses_recuperacion'], 0)
        self.assertEqual(zero_initial['semaforo'], 'verde')

    def test_conditional_formalization_modules_only_activate_when_applicable(self):
        normal = _project_steps(DEFAULT_ROUTES, 'normal', {'tiene_local': 'no', 'contratara_personal': 'no'})
        codes = {step['codigo'] for step in normal}
        self.assertNotIn('F4', codes)
        self.assertNotIn('F5', codes)
        self.assertIn('F1', codes)
        applicable = _project_steps(DEFAULT_ROUTES, 'normal', {'tiene_local': 'si', 'contratara_personal': 'si'})
        applicable_codes = {step['codigo'] for step in applicable}
        self.assertIn('F4', applicable_codes)
        self.assertIn('F5', applicable_codes)


if __name__ == '__main__':
    unittest.main()
