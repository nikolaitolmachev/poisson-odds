"""Test probabilities, reference odds, and betting line filtering."""

import unittest

from poisson_odds.poisson import Poisson


class TestPoissonProbabilities(unittest.TestCase):
    def setUp(self):
        self.model = Poisson(quality_team_a=1.5, quality_team_b=0.7)

    def test_moneyline_odds(self):
        """Checks that the odds for Team A to win are lower than for Team B to win, given that
        quality_team_A > quality_team_B in setUp. Note: This may not always be true if a draw is very likely."""
        moneyline_odds = self.model.moneyline
        self.assertLessEqual(moneyline_odds.odds_home, moneyline_odds.odds_away)

    def test_moneyline_reference_odds(self) -> None:
        """Preserve all three moneyline odds for representative qualities."""
        cases = (
            (1.1, 2.1, (5.291, 4.878, 1.669)),
            (1.5, 0.7, (1.776, 3.802, 5.780)),
            (3.05, 3.25, (2.564, 6.173, 2.237)),
            (4.0, 4.0, (2.353, 6.993, 2.353)),
            (8.0, 1.0, (1.139, 166.639, 499.750)),
            (1.0, 8.0, (499.750, 166.639, 1.139)),
        )
        for home, away, expected in cases:
            with self.subTest(home=home, away=away):
                odds = Poisson(home, away).moneyline
                self.assertEqual(
                    (odds.odds_home, odds.odds_draw, odds.odds_away), expected,
                )

    def test_probability_table_sums_to_1(self):
        """Checks that the sum of all probabilities (home goals & away goals)
        in a probability table is equal to 1 (or very close to 1)."""
        home_goals_probability = self.model.probability_table_goal_draws[0]
        away_goals_probability = self.model.probability_table_goal_draws[1]
        self.assertAlmostEqual(round(sum(home_goals_probability), 2), 1.0)
        self.assertAlmostEqual(round(sum(away_goals_probability), 2), 1.0)

    def test_total_odds(self):
        """Checks that the Total "over" increases, and the Total "under" decreases
        as the Total increases (... 2.5, 2.75, 3.00, 3.25 ...). Note: compares odds."""

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

    def test_total_reference_odds(self) -> None:
        """Preserve half, integer, quarter, and special 3.5 total odds."""
        cases = (
            (1.1, 2.1, (
                (2.5, 1.616, 2.625),
                (3.0, 1.961, 2.040),
                (3.25, 2.243, 1.848),
                (3.5, 2.525, 1.656),
            )),
            (1.5, 0.7, (
                (1.5, 1.550, 2.817),
                (2.0, 1.946, 2.059),
                (2.25, 2.303, 1.831),
            )),
            (3.05, 3.25, (
                (4.25, 1.250, 5.453),
                (6.0, 1.908, 2.100),
                (6.25, 2.091, 1.943),
            )),
            (4.0, 4.0, (
                (7.5, 1.835, 2.198),
                (8.0, 2.119, 1.895),
                (8.25, 2.288, 1.790),
            )),
        )
        for home, away, lines in cases:
            totals = Poisson(home, away).calculate_total_odds_by_poisson()
            for line, over, under in lines:
                with self.subTest(home=home, away=away, line=line):
                    self.assertIn(line, totals)
                    total = totals[line]
                    self.assertEqual(total.line, line)
                    self.assertEqual(
                        (total.odds_over, total.odds_under), (over, under),
                    )

    def test_handicap_odds(self):
        """Special cases of comparison of handicap odds according to setUp."""

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

    def test_handicap_reference_odds(self) -> None:
        """Preserve signed, zero, and quarter handicap reference odds."""
        cases = (
            (1.1, 2.1, (
                (0.5, 2.494, 1.669),
                (1.0, 1.918, 2.089),
                (1.25, 1.750, 2.403),
            )),
            (1.5, 0.7, (
                (-1.5, 3.401, 1.416),
                (-1.0, 2.486, 1.673),
                (-1.25, 2.944, 1.544),
            )),
            (3.05, 3.25, (
                (-0.5, 2.564, 1.639),
                (0.0, 2.149, 1.875),
                (0.25, 1.978, 2.056),
            )),
            (4.0, 4.0, (
                (-2.0, 4.869, 1.258),
                (0.0, 2.017, 2.017),
                (2.0, 1.258, 4.869),
            )),
            (8.0, 1.0, (
                (-7.5, 3.300, 1.435),
                (-6.75, 2.573, 1.657),
            )),
            (1.0, 8.0, (
                (7.5, 1.435, 3.300),
                (7.0, 1.538, 2.858),
                (6.75, 1.657, 2.573),
            )),
        )
        for home, away, lines in cases:
            handicaps = (
                Poisson(home, away).calculate_handicap_odds_by_poisson()
            )
            for line, home_odds, away_odds in lines:
                with self.subTest(home=home, away=away, line=line):
                    self.assertIn(line, handicaps)
                    handicap = handicaps[line]
                    self.assertEqual(handicap.line, line)
                    self.assertEqual(
                        (handicap.odds_home, handicap.odds_away),
                        (home_odds, away_odds),
                    )

    def test_low_odds_lines_are_filtered_out(self) -> None:
        """Exclude selected calculated lines with odds below the threshold."""
        cases = (
            (1.5, 0.7, (1.0, 3.5), (-2.0, 0.5)),
            (3.05, 3.25, (4.0, 8.5), (-2.0, 2.0)),
            (8.0, 1.0, (6.0, 11.5), (-8.5, -3.0)),
        )
        for home, away, total_lines, handicap_lines in cases:
            model = Poisson(home, away)
            totals = model.calculate_total_odds_by_poisson()
            handicaps = model.calculate_handicap_odds_by_poisson()
            for line in total_lines:
                with self.subTest(home=home, away=away, total=line):
                    self.assertNotIn(line, totals)
            for line in handicap_lines:
                with self.subTest(home=home, away=away, handicap=line):
                    self.assertNotIn(line, handicaps)


if __name__ == '__main__':
    unittest.main()
