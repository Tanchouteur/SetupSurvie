import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_tool_eval import divide_with_remainder


class CalculationTests(unittest.TestCase):
    def test_reserve_has_exact_remainder(self):
        result = divide_with_remainder(600, 18)
        self.assertEqual(result['complete_units'], 33)
        self.assertEqual(result['remainder'], 6)

    def test_decimal_inputs_avoid_float_rounding(self):
        result = divide_with_remainder(0.3, 0.1)
        self.assertEqual(result['complete_units'], 3)
        self.assertEqual(result['remainder'], 0)

    def test_invalid_and_non_numeric_arguments_are_rejected(self):
        for total, per_unit in [(1, 0), (-1, 2), (True, 2), ('600', 18), (float('inf'), 1), (1, float('nan')), (10**1000, 1)]:
            with self.subTest(total=total, per_unit=per_unit):
                with self.assertRaises(ValueError):divide_with_remainder(total, per_unit)


if __name__ == '__main__':unittest.main()
