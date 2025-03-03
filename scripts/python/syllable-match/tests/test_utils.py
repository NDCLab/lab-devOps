import unittest

import pandas as pd

from syllable_match.utils import compute_window_indicator


class TestComputeWindowIndicator(unittest.TestCase):
    def test_basic_case(self):
        series = pd.Series([0, 0, 1, 0, 0, 0, 0, 1, 0, 0])
        before, after = compute_window_indicator(series, window=7)
        expected_before = [0, 0, 0, 1, 1, 1, 1, 1, 1, 1]
        expected_after = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        self.assertEqual(before, expected_before)
        self.assertEqual(after, expected_after)

    def test_all_zeros(self):
        series = pd.Series([0, 0, 0, 0, 0])
        before, after = compute_window_indicator(series, window=2)
        expected_before = [0, 0, 0, 0, 0]
        expected_after = [0, 0, 0, 0, 0]
        self.assertEqual(before, expected_before)
        self.assertEqual(after, expected_after)

    def test_all_ones(self):
        series = pd.Series([1, 1, 1, 1, 1])
        before, after = compute_window_indicator(series, window=2)
        expected_before = [0, 1, 1, 1, 1]
        expected_after = [1, 1, 1, 1, 0]
        self.assertEqual(before, expected_before)
        self.assertEqual(after, expected_after)

    def test_edge_case(self):
        series = pd.Series([1])
        before, after = compute_window_indicator(series, window=1)
        expected_before = [0]
        expected_after = [0]
        self.assertEqual(before, expected_before)
        self.assertEqual(after, expected_after)

    def test_large_window(self):
        series = pd.Series([0, 1, 0, 0, 1, 0])
        before, after = compute_window_indicator(series, window=10)
        expected_before = [0, 0, 1, 1, 1, 1]
        expected_after = [1, 1, 1, 1, 0, 0]
        self.assertEqual(before, expected_before)
        self.assertEqual(after, expected_after)


if __name__ == "__main__":
    unittest.main()
