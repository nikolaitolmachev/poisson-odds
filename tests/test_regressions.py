"""Test corrected high totals and the minus-seven handicap."""

import unittest

from poisson_odds.poisson import Poisson


class TestPoissonRegressions(unittest.TestCase):
    """Check odds affected by omitted scores and the handicap fallback."""

    def test_total_8_5_includes_off_diagonal_scores(self) -> None:
        """Include scores 3:5 and 5:3 in the cumulative probability."""
        totals = Poisson(4.5, 4.5).calculate_total_odds_by_poisson()

        self.assertIn(8.5, totals)
        self.assertEqual(totals[8.5].odds_over, 1.842)
        self.assertEqual(totals[8.5].odds_under, 2.188)

    def test_total_10_5_includes_off_diagonal_scores(self) -> None:
        """Include scores 4:6 and 6:4 after the corrected total 8.5."""
        totals = Poisson(4.5, 4.5).calculate_total_odds_by_poisson()

        self.assertIn(10.5, totals)
        self.assertEqual(totals[10.5].odds_over, 3.378)
        self.assertEqual(totals[10.5].odds_under, 1.420)

    def test_handicap_minus_7_uses_normal_formula(self) -> None:
        """Use the normal denominator when calculating handicap -7.0."""
        handicaps = Poisson(8.0, 1.0).calculate_handicap_odds_by_poisson()

        self.assertIn(-7.0, handicaps)
        self.assertEqual(handicaps[-7.0].odds_home, 2.858)
        self.assertEqual(handicaps[-7.0].odds_away, 1.538)

    def test_asian_handicap_uses_corrected_minus_7(self) -> None:
        """Average adjacent odds using the corrected handicap -7.0."""
        handicaps = Poisson(8.0, 1.0).calculate_handicap_odds_by_poisson()

        self.assertIn(-7.25, handicaps)
        self.assertEqual(handicaps[-7.25].odds_home, 3.079)
        self.assertEqual(handicaps[-7.25].odds_away, 1.486)


if __name__ == '__main__':
    unittest.main()
