import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analysis import prepare_data, analyse, rating_balance


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(Path(__file__).resolve().parents[1] / 'data/raw/sales_feedback_raw.csv')

    def test_current_control_totals(self):
        t = analyse(prepare_data(self.raw))
        self.assertEqual(int(t['kpi_summary'].iloc[0].revenue), int(self.raw.revenue.sum()))
        self.assertEqual(int(t['response_analysis'].orders.sum()), len(self.raw))
        self.assertEqual(t['action_plan'].focus.iloc[0], t['product_metrics']['product'].iloc[0])

    def test_missing_column_and_duplicate_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing required columns'): prepare_data(self.raw.drop(columns='rating'))
        with self.assertRaisesRegex(ValueError, 'duplicates'): prepare_data(pd.concat([self.raw, self.raw.head(1)]))

    def test_rating_bounds(self):
        raw = self.raw.head(1).copy(); raw.loc[:, 'rating'] = 6
        with self.assertRaisesRegex(ValueError, 'rating'): prepare_data(raw)

    def test_zero_response_is_included_and_zero_revenue_is_unavailable(self):
        raw = self.raw.head(1).copy(); raw.loc[:, 'response_time_hours'] = 0; raw.loc[:, 'revenue'] = 0
        df = prepare_data(raw)
        self.assertTrue(pd.isna(df.margin_pct.iloc[0]))
        self.assertEqual(int(analyse(df)['response_analysis'].orders.sum()), 1)

    def test_balance_definition(self):
        self.assertAlmostEqual(rating_balance(pd.Series([5, 4, 1])), 0)


if __name__ == '__main__': unittest.main()
