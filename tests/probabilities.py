import unittest
from poisson_odds.poisson import Poisson


class TestPoissonProbabilities(unittest.TestCase):
    def setUp(self):
        self.model = Poisson(quality_team_a=1.5, quality_team_b=0.7)

    def test_moneyline_odds(self):
        """
        Checks that the odds for Team A to win are lower than for Team B to win, given that
        quality_team_A > quality_team_B in setUp. Note: This may not always be true if a draw is very likely.
        """
        moneyline_odds = self.model.moneyline
        self.assertLessEqual(moneyline_odds.odds_home, moneyline_odds.odds_away)

    def test_probability_table_sums_to_1(self):
        """
        Checks that the sum of all probabilities (home goals & away goals) in a probability table is equal to 1
        (or very close to 1).
        """
        home_goals_probability = self.model.probability_table_goal_draws[0]
        away_goals_probability = self.model.probability_table_goal_draws[1]
        self.assertAlmostEqual(round(sum(home_goals_probability), 2), 1.0)
        self.assertAlmostEqual(round(sum(away_goals_probability), 2), 1.0)

    def test_total_odds(self):
        """
        Checks that the Total "over" increases, and the Total "under" decreases
        as the Total increases (... 2.5, 2.75, 3.00, 3.25 ...). Note: compares odds.
        """

        totals = [value for key, value in self.model.calculate_total_odds_by_poisson().items()]
        over_odds = []
        under_odds = []

        for total in totals:
            over_odds.append(total.odds_over)
            under_odds.append(total.odds_under)

        for i in range(len(over_odds) - 1):
            self.assertLessEqual(over_odds[i], over_odds[i + 1])

        for i in range(len(under_odds) - 1):
            self.assertGreaterEqual(under_odds[i], under_odds[i + 1])

    def test_handicap_odds(self):
        """
        Special cases of comparison of handicap odds according to setUp.
        """

        all_handicaps = self.model.calculate_handicap_odds_by_poisson()
        # It can be from -11.00 to +11.00 so just take some special cases

        # 1.5 is not greater than 0.7 so odds for handicap home must be much greater than away.
        handi_minus_1_75 = all_handicaps.get(-1.75)
        self.assertGreater(handi_minus_1_75.odds_home, handi_minus_1_75.odds_away)

        # almost the same as before
        handi_minus_1 = all_handicaps.get(-1)
        self.assertGreater(handi_minus_1.odds_home, handi_minus_1.odds_away)

        # it must be equal with home win from moneyline
        handi_minus_0_5 = all_handicaps.get(-0.5)
        self.assertEqual(handi_minus_0_5.odds_home, self.model.moneyline.odds_home)

        # 1.5 is greater than 0.7 so odds for handicap home must be much lower than away.
        handi_0 = all_handicaps.get(0.0)
        self.assertLess(handi_0.odds_home, handi_0.odds_away)

        # the same as before
        handi_plus_0_25 = all_handicaps.get(0.25)
        self.assertLess(handi_plus_0_25.odds_home, handi_plus_0_25.odds_away)


if __name__ == '__main__':
    unittest.main()
