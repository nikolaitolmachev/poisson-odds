import unittest
from poisson_odds.poisson import Poisson


class TestPoissonArbitrage(unittest.TestCase):
    def setUp(self):
        self.model = Poisson(quality_team_a=1.15, quality_team_b=1.88)

    def test_no_arbitrage_in_moneyline(self):
        """Checks that there is no arbitrage situation in moneyline, that is,
        the sum of the inverse probabilities is less than or equal to 1."""
        prob_team_a = round(1 / self.model.moneyline.odds_home, 2)
        prob_team_b = round(1 / self.model.moneyline.odds_away, 2)
        prob_draw = round(1 / self.model.moneyline.odds_draw, 2)
        self.assertLessEqual(prob_team_a + prob_team_b + prob_draw, 1.0)

    def test_no_arbitrage_in_totals(self):
        """Checks that there is no arbitrage situation in totals, that is,
        the sum of the inverse probabilities is less than or equal to 1."""
        totals = [value for key, value in self.model.calculate_total_odds_by_poisson().items()]
        for total in totals:
            prob_over = round(1 / total.odds_over, 2)
            prob_under = round(1 / total.odds_under, 2)
            self.assertLessEqual(prob_over + prob_under, 1.0)

    def test_no_arbitrage_in_handicaps(self):
        """Checks that there is no arbitrage situation in handicaps, that is,
        the sum of the inverse probabilities is less than or equal to 1."""
        handicaps = [value for key, value in self.model.calculate_handicap_odds_by_poisson().items()]
        for handi in handicaps:
            prob_home = round(1 / handi.odds_home, 2)
            prob_away = round(1 / handi.odds_away, 2)
            self.assertLessEqual(prob_home + prob_away, 1.0)


if __name__ == '__main__':
    unittest.main()
