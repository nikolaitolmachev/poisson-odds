import unittest

from poisson_odds.poisson import Poisson


class TestPoissonInitialization(unittest.TestCase):

    def test_valid_initialization(self):
        """
        Checks that the class was successfully initialized with correct values.
        """
        model = Poisson(quality_team_a=1.12, quality_team_b=1.48)
        self.assertIsNotNone(model.probability_table_goal_draws)
        self.assertIsNotNone(model.moneyline)

    def test_invalid_quality_type(self):
        """
        Checks that passing an invalid data raises a ValueError.
        """
        with self.assertRaises(ValueError):
            # noinspection PyTypeChecker
            Poisson(quality_team_a="abc", quality_team_b=1.48)

    def test_negative_quality(self):
        """
        Checks that passing a negative value raises a ValueError.
        """
        with self.assertRaises(ValueError):
            Poisson(quality_team_a=1.75, quality_team_b=-1.38)

    def test_quality_too_high_warning(self):
        """
        Checks that passing values that are not real raises a warning.
        """
        with self.assertWarns(UserWarning):
            Poisson(quality_team_a=6.0, quality_team_b=4.5)


if __name__ == '__main__':
    unittest.main()
