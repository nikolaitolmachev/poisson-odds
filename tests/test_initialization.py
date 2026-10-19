"""Test Poisson initialization, input validation, and warnings."""

import unittest

from poisson_odds.poisson import Poisson


class TestPoissonInitialization(unittest.TestCase):

    def test_valid_initialization(self):
        """Checks that the class was successfully initialized with correct values."""
        model = Poisson(quality_team_a=1.12, quality_team_b=1.48)
        self.assertIsNotNone(model.probability_table_goal_draws)
        self.assertIsNotNone(model.moneyline)

    def test_invalid_quality_type(self):
        """Checks that passing an invalid data raises a ValueError."""
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            Poisson(quality_team_a="abc", quality_team_b=1.48)

    def test_negative_quality(self):
        """Checks that passing a negative value raises a ValueError."""
        with self.assertRaises(ValueError):
            Poisson(quality_team_a=1.75, quality_team_b=-1.38)

    def test_quality_too_high_warning(self):
        """Checks that passing values that are not real raises a warning."""
        with self.assertWarns(UserWarning):
            Poisson(quality_team_a=6.0, quality_team_b=4.5)

    def test_positive_numeric_qualities(self) -> None:
        """Accept positive integers and finite floats in either position."""
        for home, away in ((1, 2), (1.5, 2), (1, 2.5), (1.5, 2.5)):
            with self.subTest(home=home, away=away):
                model = Poisson(home, away)
                self.assertIsNotNone(model.moneyline)

    def test_nonpositive_qualities(self) -> None:
        """Reject zero and negative qualities for either team."""
        for value in (0, 0.0, -1, -0.5):
            for home, away in ((value, 1.0), (1.0, value)):
                with self.subTest(home=home, away=away):
                    with self.assertRaises(ValueError):
                        Poisson(home, away)

    def test_nonfinite_qualities(self) -> None:
        """Reject NaN and both infinities for either team."""
        for value in (float("nan"), float("inf"), float("-inf")):
            for home, away in ((value, 1.0), (1.0, value)):
                with self.subTest(home=home, away=away):
                    with self.assertRaisesRegex(
                        ValueError,
                        "^Incorrect quality value for one of teams at least!$",
                    ):
                        Poisson(home, away)

    def test_boolean_qualities(self) -> None:
        """Preserve acceptance of True and rejection of False."""
        for home, away in ((True, 1.0), (1.0, True), (True, True)):
            with self.subTest(home=home, away=away):
                model = Poisson(home, away)
                self.assertIsNotNone(model.moneyline)
        for home, away in ((False, 1.0), (1.0, False)):
            with self.subTest(home=home, away=away):
                with self.assertRaises(ValueError):
                    Poisson(home, away)

    def test_integer_too_large_for_float(self) -> None:
        """Reject huge integers with ValueError rather than OverflowError."""
        value = 10 ** 1000
        for home, away in ((value, 1.0), (1.0, value)):
            with self.subTest(home=home, away=away):
                with self.assertRaisesRegex(
                    ValueError,
                    "^Incorrect quality value for one of teams at least!$",
                ):
                    Poisson(home, away)

    def test_warning_at_and_above_threshold(self) -> None:
        """Warn when the sum of finite qualities reaches or exceeds ten."""
        for home, away in ((5.0, 5.0), (6.0, 4.5)):
            with self.subTest(home=home, away=away):
                with self.assertWarns(UserWarning):
                    Poisson(home, away)


if __name__ == '__main__':
    unittest.main()
