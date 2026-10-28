import unittest
from datetime import date
from types import SimpleNamespace
from app.modules.incubadora.services import next_review, inactive


class IncubadoraRulesTest(unittest.TestCase):
    def test_review_calendar_boundaries(self):
        self.assertEqual(next_review(date(2028, 1, 31), 'mensual'), date(2028, 2, 29))
        self.assertEqual(next_review(date(2027, 1, 31), 'mensual'), date(2027, 2, 28))
        self.assertEqual(next_review(date(2026, 12, 31), 'mensual'), date(2027, 1, 31))
        self.assertEqual(next_review(date(2026, 12, 31), 'cada 15 días'), date(2027, 1, 15))
        with self.assertRaises(ValueError):
            next_review(date(2026, 1, 1), 'otro')

    def test_inactivity_exact_boundary_and_no_unapproved_default(self):
        folder = SimpleNamespace(estado='activo', ultimo_movimiento=date(2026, 1, 1))
        self.assertFalse(inactive(folder, None, date(2026, 12, 31)))
        self.assertFalse(inactive(folder, 15, date(2026, 1, 15)))
        self.assertTrue(inactive(folder, 15, date(2026, 1, 16)))
        folder.estado = 'formalizado'
        self.assertFalse(inactive(folder, 15, date(2026, 12, 31)))
