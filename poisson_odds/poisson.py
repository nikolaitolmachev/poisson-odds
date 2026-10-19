import math
import warnings
from tabulate import tabulate

from poisson_odds.probability import Probability
import poisson_odds.consts as consts
from poisson_odds.bookmaker_moneyline import BookmakerMoneyline
from poisson_odds.bookmaker_total import BookmakerTotal
from poisson_odds.bookmaker_handicap import BookmakerHandicap


class Poisson:
    """Calculate betting odds from team scoring probabilities.

    Attributes:
        _probability_table_goal_draws: Home, away, and matching-score
            probabilities, in that order.
        _moneyline: Odds for a home win, draw, and away win.
    """

    def __init__(self, quality_team_a: float, quality_team_b: float) -> None:
        """Initialize the probability table and moneyline odds.

        Args:
            quality_team_a: Expected goals for the home team.
            quality_team_b: Expected goals for the away team.

        Raises:
            ValueError: If either quality is not a positive int or float.

        Warns:
            UserWarning: If the sum of team qualities is at least 10.
        """
        if all(
            isinstance(value, (float, int)) and value > 0
            for value in (quality_team_a, quality_team_b)
        ):
            if quality_team_a + quality_team_b >= 10:
                warnings.warn(
                    "Values aren't real so it can't guarantee to work correctly.",
                    UserWarning,
                    2,
                )
            self._probability_table_goal_draws: list[list[Probability]] = (
                self._create_probability_table(quality_team_a, quality_team_b)
            )
            self._moneyline: BookmakerMoneyline = self._calculate_moneyline_by_poisson()
        else:
            raise ValueError(
                'Incorrect quality value for one of teams at least!'
            )

    @property
    def probability_table_goal_draws(self) -> list[list[Probability]]:
        """Return the original, mutable probability table."""
        return self._probability_table_goal_draws

    @property
    def moneyline(self) -> BookmakerMoneyline:
        """Return the calculated moneyline odds."""
        return self._moneyline

    @staticmethod
    def _calculate_goal_probability(_lambda: float, k: int) -> Probability:
        """Calculate the probability of a team scoring a given goal count.

        Args:
            _lambda: Expected number of goals.
            k: Number of goals.

        Returns:
            Poisson probability rounded to three decimal places.
        """
        probability_k = (_lambda ** k * math.exp(-_lambda)) / (math.factorial(k))

        return Probability(round(probability_k, 3))

    @staticmethod
    def _calculate_draw_probability(
        goal_probability_home: Probability,
        goal_probability_away: Probability,
    ) -> Probability:
        """Calculate the probability of a matching score for both teams.

        Args:
            goal_probability_home: Probability of the home goal count.
            goal_probability_away: Probability of the same away goal count.

        Returns:
            Matching-score probability rounded to three decimal places.
        """
        draw_probability = goal_probability_home * goal_probability_away
        return Probability(round(draw_probability, 3))

    def _create_probability_table(
        self, quality_team_a: float, quality_team_b: float,
    ) -> list[list[Probability]]:
        """Build the home, away, and matching-score probability rows.

        Args:
            quality_team_a: Expected goals for the home team.
            quality_team_b: Expected goals for the away team.

        Returns:
            Three rows of Probability objects, each containing
            MAX_SCORE_TO_COUNT elements in ascending goal-count order.
        """
        goal_counts = range(consts.MAX_SCORE_TO_COUNT)
        home = [
            self._calculate_goal_probability(quality_team_a, goals)
            for goals in goal_counts
        ]
        away = [
            self._calculate_goal_probability(quality_team_b, goals)
            for goals in goal_counts
        ]
        draws = [
            self._calculate_draw_probability(
                home_probability, away_probability,
            )
            for home_probability, away_probability in zip(home, away)
        ]
        return [home, away, draws]

    def calculate_total_odds_by_poisson(self) -> dict:
        """Calculate over/under odds from the probability table.

        Returns:
            BookmakerTotal objects keyed by line in ascending order, after
            filtering out lines with odds below the minimum threshold.

        Raises:
            ZeroDivisionError: If an unguarded denominator is zero.
        """

        list_of_totals = []

        # calculate 0.5, 1.5, 2.5 ... 8.5 lines

        under = self._probability_table_goal_draws[2][0].probability
        if not under:
            under = consts.AROUND_ZERO
        list_of_totals.append(BookmakerTotal(0.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        under = self._probability_table_goal_draws[2][0] + self._probability_table_goal_draws[0][1] * \
                self._probability_table_goal_draws[1][0] + self._probability_table_goal_draws[0][0] * \
                self._probability_table_goal_draws[1][1]
        if not under:
            under = consts.AROUND_ZERO
        list_of_totals.append(BookmakerTotal(1.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        under += self._probability_table_goal_draws[2][1] + self._probability_table_goal_draws[0][2] * \
                 self._probability_table_goal_draws[1][0] + self._probability_table_goal_draws[0][0] * \
                 self._probability_table_goal_draws[1][2]
        list_of_totals.append(BookmakerTotal(2.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        under += round(self._probability_table_goal_draws[0][2] * self._probability_table_goal_draws[1][1] +
                       self._probability_table_goal_draws[0][1] * self._probability_table_goal_draws[1][2] +
                       self._probability_table_goal_draws[0][3] * self._probability_table_goal_draws[1][0] +
                       self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][3], 4)
        list_of_totals.append(BookmakerTotal(3.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = self._probability_table_goal_draws[2][2]
        j = 4
        for i in range(0, 5):
            if i == 2:
                j -= 1
                continue
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(4.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = 0
        j = 5
        for i in range(0, 6):
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(5.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = self._probability_table_goal_draws[2][3]
        j = 6
        for i in range(0, 7):
            if i == 3:
                j -= 1
                continue
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(6.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = 0
        j = 7
        for i in range(0, 8):
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(7.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = self._probability_table_goal_draws[2][4]
        j = 8
        for i in range(0, 9):
            if i == 4:
                j -= 1
                continue
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(8.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = 0
        j = 9
        for i in range(0, 10):
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(9.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = self._probability_table_goal_draws[2][5]
        j = 10
        for i in range(0, 11):
            if i == 5:
                j -= 1
                continue
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(10.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        temp = 0
        j = 11
        for i in range(0, 12):
            temp += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
            j -= 1
        under += temp
        list_of_totals.append(BookmakerTotal(11.5, Poisson.get_opposite_odds(under), round(1 / under, 3)))

        # calculate 1.0, 2.0, 3.00 ... 11.00 lines
        under1 = round(1 / ((1 / list_of_totals[0].odds_under) / (1 / list_of_totals[0].odds_under +
                                                                  1 / list_of_totals[1].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(1, Poisson.get_opposite_odds(1 / under1), under1))

        under2 = round(1 / ((1/list_of_totals[1].odds_under) / (1/list_of_totals[1].odds_under +
                                                                1/list_of_totals[2].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(2, Poisson.get_opposite_odds(1 / under2), under2))

        under3 = round(1 / ((1/list_of_totals[2].odds_under) / (1/list_of_totals[2].odds_under +
                                                                1/list_of_totals[3].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(3, Poisson.get_opposite_odds(1 / under3), under3))

        under4 = round(1 / ((1 / list_of_totals[3].odds_under) / (1 / list_of_totals[3].odds_under +
                                                                  1 / list_of_totals[4].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(4, Poisson.get_opposite_odds(1 / under4), under4))

        under5 = round(1 / ((1 / list_of_totals[4].odds_under) / (1 / list_of_totals[4].odds_under +
                                                                  1 / list_of_totals[5].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(5, Poisson.get_opposite_odds(1 / under5), under5))

        under6 = round(1 / ((1 / list_of_totals[5].odds_under) / (1 / list_of_totals[5].odds_under +
                                                                  1 / list_of_totals[6].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(6, Poisson.get_opposite_odds(1 / under6), under6))

        under7 = round(1 / ((1 / list_of_totals[6].odds_under) / (1 / list_of_totals[6].odds_under +
                                                                  1 / list_of_totals[7].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(7, Poisson.get_opposite_odds(1 / under7), under7))

        under8 = round(1 / ((1 / list_of_totals[7].odds_under) / (1 / list_of_totals[7].odds_under +
                                                                  1 / list_of_totals[8].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(8, Poisson.get_opposite_odds(1 / under8), under8))

        under9 = round(1 / ((1 / list_of_totals[8].odds_under) / (1 / list_of_totals[8].odds_under +
                                                                  1 / list_of_totals[9].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(9, Poisson.get_opposite_odds(1 / under9), under9))

        under10 = round(1 / ((1 / list_of_totals[9].odds_under) / (1 / list_of_totals[9].odds_under +
                                                                   1 / list_of_totals[10].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(10, Poisson.get_opposite_odds(1 / under10), under10))

        under11 = round(1 / ((1 / list_of_totals[10].odds_under) / (1 / list_of_totals[10].odds_under +
                                                                    1 / list_of_totals[11].odds_over)), 3)
        list_of_totals.append(BookmakerTotal(11, Poisson.get_opposite_odds(1 / under11), under11))

        list_of_totals = sorted(list_of_totals, key=lambda bookmaker_total: bookmaker_total.line)

        # calculate 0.75, 1.25, 1.75, 2.25 ... 11.25 lines
        i = 1
        asian_lines = []
        for bt in list_of_totals:
            try:
                asian_total_line = self._get_asian_total_line(bt, list_of_totals[i])
                asian_lines.append(asian_total_line)
                i += 1
            except IndexError:
                break
        list_of_totals = sorted(list_of_totals + asian_lines, key=lambda bookmaker_total: bookmaker_total.line)

        # remove low odds
        list_of_totals = BookmakerTotal.get_only_meaningful_lines(list_of_totals)

        # create dict
        dict_totals = {}
        for total in list_of_totals:
            dict_totals[total.line] = total

        return dict_totals

    @staticmethod
    def _get_asian_total_line(total_1: BookmakerTotal, total_2: BookmakerTotal) -> BookmakerTotal:
        """Calculate an Asian total by averaging adjacent lines and odds.

        Args:
            total_1: First neighboring total.
            total_2: Second neighboring total.

        Returns:
            Total with its line rounded to two decimal places and odds to
            three decimal places.
        """
        line = round((total_1.line + total_2.line) / 2, 2)
        over = round((total_1.odds_over + total_2.odds_over) / 2, 3)
        under = round((total_1.odds_under + total_2.odds_under) / 2, 3)
        return BookmakerTotal(line, over, under)

    def _calculate_moneyline_by_poisson(self) -> BookmakerMoneyline:
        """Calculate moneyline odds from the probability table.

        Returns:
            BookmakerMoneyline containing home win, draw, and away win odds.
        """

        # calculate odds for home win
        home_odds = consts.AROUND_ZERO
        i, j = 1, 0
        for _ in range(0, consts.MAX_SCORE_TO_COUNT - 1):
            for _ in range(0, consts.MAX_SCORE_TO_COUNT):
                if i != j:
                    res = self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
                    home_odds += res
                    j += 1
            i += 1
            j = 0
        home_odds = round(1/home_odds, 3)

        # calculate odds for a draw
        draw_odds = consts.AROUND_ZERO
        for draw in self._probability_table_goal_draws[2]:
            draw_odds += draw.probability
        draw_odds = round(1/draw_odds, 3)

        # calculate odds for away win
        away_odds = consts.AROUND_ZERO
        i, j = 0, 1
        for _ in range(0, consts.MAX_SCORE_TO_COUNT - 1):
            for _ in range(0, consts.MAX_SCORE_TO_COUNT):
                if i != j:
                    res = self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][j]
                    away_odds += res
                    i += 1
            j += 1
            i = 0
        away_odds = round(1 / away_odds, 3)

        return BookmakerMoneyline(home_odds, draw_odds, away_odds)

    def calculate_handicap_odds_by_poisson(self) -> dict:
        """Calculate handicap odds from the probability table.

        Returns:
            BookmakerHandicap objects keyed by line in ascending order, after
            filtering out lines with odds below the minimum threshold.

        Raises:
            ZeroDivisionError: If an unguarded denominator is zero.
        """

        list_of_handicaps = []

        # calculate -10.5, -6.5, -5.5 ... +10.5 lines

        # -10.5 = 11-0
        handicap_minus_10_5 = self._probability_table_goal_draws[0][11] * self._probability_table_goal_draws[1][0]
        if handicap_minus_10_5:
            list_of_handicaps.append(BookmakerHandicap(-10.5, round(1 / handicap_minus_10_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_10_5)))

        # -9.5 = 10-0, 11-0, 11-1
        handicap_minus_9_5 = self._probability_table_goal_draws[0][10] * self._probability_table_goal_draws[1][0] + \
                            self._probability_table_goal_draws[0][11] * self._probability_table_goal_draws[1][0] + \
                            self._probability_table_goal_draws[0][11] * self._probability_table_goal_draws[1][1]
        if handicap_minus_9_5:
            list_of_handicaps.append(BookmakerHandicap(-9.5, round(1 / handicap_minus_9_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_9_5)))

        # -8.5 = 9-0, 10-0, 10-1, 11-0, 11-1, 11-2
        handicap_minus_8_5 = 0.0
        for i in range(9, 12):
            for j in range(min(3, i - 8)):
                handicap_minus_8_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_8_5:
            list_of_handicaps.append(BookmakerHandicap(-8.5, round(1 / handicap_minus_8_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_8_5)))

        # -7.5 = 8-0, 9-0, 9-1, 10-0, 10-1, 10-2, 11-0, 11-1, 11-2, 11-3
        handicap_minus_7_5 = 0.0
        for i in range(8, 12):
            for j in range(min(4, i - 7)):
                handicap_minus_7_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_7_5:
            list_of_handicaps.append(BookmakerHandicap(-7.5, round(1 / handicap_minus_7_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_7_5)))

        # -6.5 = 7-0, 8-0, 8-1, 9-0, 9-1, 9-2,  10-0, 10-1, 10-2, 10-3, 11-0, 11-1, 11-2, 11-3, 11-4
        handicap_minus_6_5 = 0.0
        for i in range(7, 12):
            for j in range(min(5, i - 6)):
                handicap_minus_6_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_6_5:
            list_of_handicaps.append(BookmakerHandicap(-6.5, round(1 / handicap_minus_6_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_6_5)))

        # -5.5 = 6-0, 7-0, 7-1, 8-0, 8-1, 8-2, 9-0, 9-1, 9-2, 9-3, 10-0, 10-1, 10-2, 10-3, 10-4, 11-0, 11-1, 11-2,
        #       11-3, 11-4, 11-5
        handicap_minus_5_5 = 0.0
        for i in range(6, 12):
            for j in range(min(6, i - 5)):
                handicap_minus_5_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_5_5:
            list_of_handicaps.append(BookmakerHandicap(-5.5, round(1 / handicap_minus_5_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_5_5)))

        # -4.5 = 5-0, 6-0, 6-1, 7-0, 7-1, 7-2, 8-0, 8-1, 8-2, 8-3, 9-0, 9-1, 9-2, 9-3, 9-4
        #           10-0, 10-1, 10-2, 10-3, 10-4, 10-5, 11-0, 11-1, 11-2, 11-3, 11-4, 11-5, 11-6
        handicap_minus_4_5 = 0.0
        for i in range(5, 12):
            for j in range(min(7, i - 4)):
                handicap_minus_4_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_4_5:
            list_of_handicaps.append(BookmakerHandicap(-4.5, round(1 / handicap_minus_4_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_4_5)))

        # -3.5 = 4-0, 5-0, 5-1, 6-0, 6-1, 6-2, 7-0, 7-1, 7-2, 7-3, 8-0, 8-1, 8-2, 8-3, 8-4
        #       9-0, 9-1, 9-2, 9-3, 9-4, 9-5, 10-0, 10-1, 10-2, 10-3, 10-4, 10-5, 10-6, 11-0, 11-1, 11-2, 11-3,
        #       11-4, 11-5, 11-6, 11-7
        handicap_minus_3_5 = 0.0
        for i in range(4, 12):
            for j in range(min(8, i - 3)):
                handicap_minus_3_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_3_5:
            list_of_handicaps.append(BookmakerHandicap(-3.5, round(1 / handicap_minus_3_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_3_5)))

        # -2.5 = 3-0, 4-0, 4-1, 5-0, 5-1, 5-2, 6-0, 6-1, 6-2, 6-3, 7-0, 7-1, 7-2, 7-3, 7-4, 8-0, 8-1, 8-2, 8-3, 8-4. 8-5
        #       9-0, 9-1, 9-2, 9-3, 9-4, 9-5, 9-6, 10-0, 10-1, 10-2, 10-3, 10-4, 10-5, 10-6, 10-7
        #       11-0, 11-1, 11-2, 11-3, 11-4, 11-5, 11-6, 11-7, 11-8
        handicap_minus_2_5 = 0.0
        for i in range(3, 12):
            for j in range(min(9, i - 2)):
                handicap_minus_2_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_2_5:
            list_of_handicaps.append(BookmakerHandicap(-2.5, round(1 / handicap_minus_2_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_2_5)))

        # -1.5 = 2-0, 3-0, 3-1, 4-0, 4-1, 4-2, 5-0, 5-1, 5-2, 5-3, 6-0, 6-1, 6-2, 6-3, 6-4
        #      = 7-0, 7-1, 7-2, 7-3, 7-4, 7-5, 8-0, 8-1, 8-2, 8-3, 8-4, 8-5, 8-6
        #       9-0, 9-1, 9-2, 9-3, 9-4, 9-5, 9-6, 9-7, 10-0, 10-1, 10-2, 10-3, 10-4, 10-5, 10-6, 10-7, 10-8
        #       11-0, 11-1, 11-2, 11-3, 11-4, 11-5, 11-6, 11-7, 11-8, 11-9
        handicap_minus_1_5 = 0.0
        for i in range(2, 12):
            for j in range(min(10, i - 1)):
                handicap_minus_1_5 += self._probability_table_goal_draws[0][i] * \
                                      self._probability_table_goal_draws[1][j]
        if handicap_minus_1_5:
            list_of_handicaps.append(BookmakerHandicap(-1.5, round(1 / handicap_minus_1_5, 3),
                                                       Poisson.get_opposite_odds(handicap_minus_1_5)))

        # -0.5 = Moneyline home win
        list_of_handicaps.append(BookmakerHandicap(-0.5, self._moneyline.odds_home,
                                                   Poisson.get_opposite_odds(1 / self._moneyline.odds_home)))

        # +0
        handicap_0_home_odds = round((1 - (1 / self._moneyline.odds_draw)) / (1 / self._moneyline.odds_home), 3)
        handicap_0_away_odds = round((1 - (1 / self._moneyline.odds_draw)) / (1 / self._moneyline.odds_away), 3)
        list_of_handicaps.append(BookmakerHandicap(0, handicap_0_home_odds, handicap_0_away_odds))

        # +0.5 = Moneyline away win
        list_of_handicaps.append(BookmakerHandicap(0.5,
                                Poisson.get_opposite_odds(1 / self._moneyline.odds_away), self._moneyline.odds_away))

        # +1.5 = 0-2, 0-3, 1-3, 0-4, 1-4, 2-4, 0-5, 1-5, 2-5, 3-5, 0-6, 1-6, 2-6, 3-6, 4-6
        #      = 0-7, 1-7, 2-7, 3-7, 4-7, 5-7, 0-8, 1-8, 2-8. 3-8, 4-8, 5-8, 6-8
        #       0-9, 1-9, 2-9, 3-9, 4-9, 5-9, 6-9, 7-9
        #       0-10, 1-10, 2-10, 3-10, 4-10, 5-10, 6-10, 7-10, 8-10
        #       0-11, 1-11, 2-11, 3-11, 4-11, 5-11, 6-11, 7-11, 8-11, 9-11
        handicap_plus_1_5 = 0.0
        for i in range(10):
            for j in range(2, 12):
                if (i == 0 and j >= 2) or \
                        (i == 1 and j >= 3) or \
                        (i == 2 and j >= 4) or \
                        (i == 3 and j >= 5) or \
                        (i == 4 and j >= 6) or \
                        (i == 5 and j >= 7) or \
                        (i == 6 and j >= 8) or \
                        (i == 7 and j >= 9) or \
                        (i == 8 and j >= 10) or \
                        (i == 9 and j == 11):
                    handicap_plus_1_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_1_5:
            list_of_handicaps.append(BookmakerHandicap(1.5,
                                        Poisson.get_opposite_odds(handicap_plus_1_5), round(1 / handicap_plus_1_5, 3)))

        # +2.5 = 0-3, 0-4, 1-4, 0-5, 1-5, 2-5, 0-6, 1-6, 2-6, 3-6
        #      = 0-7, 1-7, 2-7, 3-7, 4-7, 0-8, 1-8, 2-8, 3-8, 4-8, 5-8
        #        0-9, 1-9, 2-9, 3-9, 4-9, 5-9, 6-9, 0-10, 1-10, 2-10, 3-10, 4-10, 5-10, 6-10, 7-10
        #        0-11, 1-11, 2-11, 3-11, 4-11, 5-11, 6-11, 7-11, 8-11
        handicap_plus_2_5 = 0.0
        for i in range(9):
            for j in range(3, 12):
                if (i == 0 and j >= 3) or \
                        (i == 1 and j >= 4) or \
                        (i == 2 and j >= 5) or \
                        (i == 3 and j >= 6) or \
                        (i == 4 and j >= 7) or \
                        (i == 5 and j >= 8) or \
                        (i == 6 and j >= 9) or \
                        (i == 7 and j >= 10) or \
                        (i == 8 and j == 11):
                    handicap_plus_2_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_2_5:
            list_of_handicaps.append(BookmakerHandicap(2.5,
                                        Poisson.get_opposite_odds(handicap_plus_2_5), round(1 / handicap_plus_2_5, 3)))

        # +3.5 = 0-4, 0-5, 1-5, 0-6, 1-6, 2-6, 0-7, 1-7, 2-7, 3-7, 0-8, 1-8, 2-8, 3-8, 4-8
        #      0-9, 1-9, 2-9, 3-9, 4-9, 5-9, 0-10, 1-10, 2-10, 3-10, 4-10, 5-10, 6-10, 0-11, 1-11, 2-11, 3-11,
        #      4-11, 5-11, 6-11, 7-11
        handicap_plus_3_5 = 0.0
        for i in range(8):
            for j in range(4, 12):
                if (i == 0 and j >= 4) or \
                        (i == 1 and j >= 5) or \
                        (i == 2 and j >= 6) or \
                        (i == 3 and j >= 7) or \
                        (i == 4 and j >= 8) or \
                        (i == 5 and j >= 9) or \
                        (i == 6 and j >= 10) or \
                        (i == 7 and j == 11):
                    handicap_plus_3_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_3_5:
            list_of_handicaps.append(BookmakerHandicap(3.5,
                                        Poisson.get_opposite_odds(handicap_plus_3_5), round(1 / handicap_plus_3_5, 3)))

        # +4.5= 0-5, 0-6, 1-6, 0-7, 1-7, 2-7, 0-8, 1-8, 2-8, 3-8, 0-9, 1-9, 2-9, 3-9, 4-9
        #       0-10, 1-10, 2-10, 3-10, 4-10, 5-10, 0-11, 1-11, 2-11, 3-11, 4-11, 5-11, 6-11
        handicap_plus_4_5 = 0.0
        for i in range(7):
            for j in range(5, 12):
                if (i == 0 and j >= 5) or \
                        (i == 1 and j >= 6) or \
                        (i == 2 and j >= 7) or \
                        (i == 3 and j >= 8) or \
                        (i == 4 and j >= 9) or \
                        (i == 5 and j >= 10) or \
                        (i == 6 and j == 11):
                    handicap_plus_4_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_4_5:
            list_of_handicaps.append(BookmakerHandicap(4.5,
                                        Poisson.get_opposite_odds(handicap_plus_4_5), round(1 / handicap_plus_4_5, 3)))

        # +5.5 = 0-6, 0-7, 1-7, 0-8, 1-8, 2-8, 0-9, 1-9, 2-9, 3-9, 0-10, 1-10, 2-10, 3-10, 4-10, 0-11, 1-11,
        # 2-11, 3-11, 4-11, 5-11
        handicap_plus_5_5 = 0.0
        for i in range(6):
            for j in range(6, 12):
                if (i == 0 and j >= 6) or \
                        (i == 1 and j >= 7) or \
                        (i == 2 and j >= 8) or \
                        (i == 3 and j >= 9) or \
                        (i == 4 and j >= 10) or \
                        (i == 5 and j == 11):
                    handicap_plus_5_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_5_5:
            list_of_handicaps.append(BookmakerHandicap(5.5,
                                        Poisson.get_opposite_odds(handicap_plus_5_5), round(1 / handicap_plus_5_5, 3)))

        # +6.5 = 0-7, 0-8, 1-8, 0-9, 1-9, 2-9, 0-10, 1-10, 2-10, 3-10, 0-11, 1-11, 2-11, 3-11, 4-11
        handicap_plus_6_5 = 0.0
        for i in range(5):
            for j in range(7, 12):
                if (i == 0 and j >= 7) or (i == 1 and j >= 8) or (i == 2 and j >= 9) or (i == 3 and j >= 10) or (
                        i == 4 and j == 11):
                    handicap_plus_6_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_6_5:
            list_of_handicaps.append(BookmakerHandicap(6.5,
                                        Poisson.get_opposite_odds(handicap_plus_6_5), round(1 / handicap_plus_6_5, 3)))

        # +7.5 = 0-8, 0-9, 1-9, 0-10, 1-10, 2-10, 0-11, 1-11, 2-11, 3-11
        handicap_plus_7_5 = 0.0
        for i in range(4):
            for j in range(8, 12):
                if (i == 0 and j >= 8) or (i == 1 and j >= 9) or (i == 2 and j >= 10) or (i == 3 and j == 11):
                    handicap_plus_7_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_7_5:
            list_of_handicaps.append(BookmakerHandicap(7.5,
                                        Poisson.get_opposite_odds(handicap_plus_7_5), round(1 / handicap_plus_7_5, 3)))

        # +8.5 = 0-9, 0-10, 1-10, 0-11, 1-11, 2-11
        handicap_plus_8_5 = 0.0
        for i in range(3):
            for j in range(9, 12):
                if (i == 0 and j >= 9) or (i == 1 and j >= 10) or (i == 2 and j == 11):
                    handicap_plus_8_5 += self._probability_table_goal_draws[0][i] * \
                                         self._probability_table_goal_draws[1][j]
        if handicap_plus_8_5:
            list_of_handicaps.append(BookmakerHandicap(8.5,
                                        Poisson.get_opposite_odds(handicap_plus_8_5), round(1 / handicap_plus_8_5, 3)))

        # +9.5 = 0-10, 0-11, 1-11
        handicap_plus_9_5 = self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][10] + \
                            self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][11] + \
                            self._probability_table_goal_draws[0][1] * self._probability_table_goal_draws[1][11]
        if handicap_plus_9_5:
            list_of_handicaps.append(BookmakerHandicap(9.5,
                                        Poisson.get_opposite_odds(handicap_plus_9_5), round(1 / handicap_plus_9_5, 3)))

        # +10.5 = 0-11
        handicap_plus_10_5 = self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][11]
        if handicap_plus_10_5:
            list_of_handicaps.append(BookmakerHandicap(10.5,
                                    Poisson.get_opposite_odds(handicap_plus_10_5), round(1 / handicap_plus_10_5, 3)))


        # calculate -11, -7, -6 ... -1 lines
        home_win_by_1 = 0.0
        for i in range(1, 12):
            home_win_by_1 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 1]
        to_home = home_win_by_1
        try:
            home_odds = round((1 - home_win_by_1) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_1) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_1) / (1 - (1 / self._moneyline.odds_home)), 3)
        list_of_handicaps.append(BookmakerHandicap(-1.0, home_odds, away_odds))

        home_win_by_2 = 0.0
        for i in range(2, 12):
            home_win_by_2 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 2]
        to_home += home_win_by_2
        to_away = home_win_by_1
        try:
            home_odds = round((1 - home_win_by_2) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_2) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_2) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-2.0, home_odds, away_odds))

        home_win_by_3 = 0.0
        for i in range(3, 12):
            home_win_by_3 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 3]
        to_home += home_win_by_3
        to_away += home_win_by_2
        try:
            home_odds = round((1 - home_win_by_3) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_3) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_3) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-3.0, home_odds, away_odds))

        home_win_by_4 = 0.0
        for i in range(4, 12):
            home_win_by_4 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 4]
        to_home += home_win_by_4
        to_away += home_win_by_3
        try:
            home_odds = round((1 - home_win_by_4) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_4) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_4) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-4.0, home_odds, away_odds))

        home_win_by_5 = 0.0
        for i in range(5, 12):
            home_win_by_5 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 5]
        to_home += home_win_by_5
        to_away += home_win_by_4
        try:
            home_odds = round((1 - home_win_by_5) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_5) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_5) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-5.0, home_odds, away_odds))

        home_win_by_6 = 0.0
        for i in range(6, 12):
            home_win_by_6 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 6]
        to_home += home_win_by_6
        to_away += home_win_by_5
        try:
            home_odds = round((1 - home_win_by_6) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_6) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_6) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-6.0, home_odds, away_odds))

        home_win_by_7 = 0.0
        for i in range(7, 12):
            home_win_by_7 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 7]
        to_home += home_win_by_7
        to_away += home_win_by_6
        try:
            home_odds = round(
                (1 - home_win_by_7)
                / ((1 / self._moneyline.odds_home) - to_home),
                3,
            )
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_7) / consts.AROUND_ZERO, 3)
        away_odds = round((1 - home_win_by_7) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-7.0, home_odds, away_odds))

        home_win_by_8 = 0.0
        for i in range(8, 12):
            home_win_by_8 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i - 8]
        to_home += home_win_by_8
        to_away += home_win_by_7
        try:
            home_odds = round((1 - home_win_by_8) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_8) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_8) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-8.0, home_odds, away_odds))

        home_win_by_9 = self._probability_table_goal_draws[0][9] * self._probability_table_goal_draws[1][0] + \
                            self._probability_table_goal_draws[0][10] * self._probability_table_goal_draws[1][1] + \
                            self._probability_table_goal_draws[0][11] * self._probability_table_goal_draws[1][2]
        to_home += home_win_by_9
        to_away += home_win_by_8
        try:
            home_odds = round((1 - home_win_by_9) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_9) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_9) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-9.0, home_odds, away_odds))

        home_win_by_10 = self._probability_table_goal_draws[0][10] * self._probability_table_goal_draws[1][0] + \
                             self._probability_table_goal_draws[0][11] * self._probability_table_goal_draws[1][1]
        to_home += home_win_by_10
        to_away += home_win_by_9
        try:
            home_odds = round((1 - home_win_by_10) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_10) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_10) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-10.0, home_odds, away_odds))

        home_win_by_11 = self._probability_table_goal_draws[0][11] * self._probability_table_goal_draws[1][0]
        to_home += home_win_by_11
        to_away += home_win_by_10
        try:
            home_odds = round((1 - home_win_by_11) / ((1 / self._moneyline.odds_home) - to_home), 3)
        except ZeroDivisionError:
            home_odds = round((1 - home_win_by_11) / consts.AROUND_ZERO, 3) # then closer to 0
        away_odds = round((1 - home_win_by_11) / (1 - (1 / self._moneyline.odds_home) + to_away), 3)
        list_of_handicaps.append(BookmakerHandicap(-11.0, home_odds, away_odds))

        # calculate +1, +2, +3 ... +11 lines
        away_win_by_1 = 0.0
        for i in range(11):
            away_win_by_1 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 1]
        to_away = away_win_by_1
        try:
            away_odds = round((1 - away_win_by_1) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_1) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_1) / (1 - (1 / self._moneyline.odds_away)), 3)
        list_of_handicaps.append(BookmakerHandicap(1.0, home_odds, away_odds))

        away_win_by_2 = 0.0
        for i in range(10):
            away_win_by_2 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 2]
        to_away += away_win_by_2
        to_home = away_win_by_1
        try:
            away_odds = round((1 - away_win_by_2) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_2) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_2) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(2.0, home_odds, away_odds))

        away_win_by_3 = 0.0
        for i in range(9):
            away_win_by_3 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 3]
        to_away += away_win_by_3
        to_home += away_win_by_2
        try:
            away_odds = round((1 - away_win_by_3) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_3) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_3) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(3.0, home_odds, away_odds))

        away_win_by_4 = 0.0
        for i in range(8):
            away_win_by_4 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 4]
        to_away += away_win_by_4
        to_home += away_win_by_3
        try:
            away_odds = round((1 - away_win_by_4) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_4) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_4) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(4.0, home_odds, away_odds))

        away_win_by_5 = 0.0
        for i in range(7):
            away_win_by_5 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 5]
        to_away += away_win_by_5
        to_home += away_win_by_4
        try:
            away_odds = round((1 - away_win_by_5) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_5) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_5) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(5.0, home_odds, away_odds))

        away_win_by_6 = 0.0
        for i in range(6):
            away_win_by_6 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 6]
        to_away += away_win_by_6
        to_home += away_win_by_5
        try:
            away_odds = round((1 - away_win_by_6) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_6) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_6) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(6.0, home_odds, away_odds))

        away_win_by_7 = 0.0
        for i in range(5):
            away_win_by_7 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 7]
        to_away += away_win_by_7
        to_home += away_win_by_6
        try:
            away_odds = round((1 - away_win_by_7) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_7) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_7) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(7.0, home_odds, away_odds))

        away_win_by_8 = 0.0
        for i in range(4):
            away_win_by_8 += self._probability_table_goal_draws[0][i] * self._probability_table_goal_draws[1][i + 8]
        to_away += away_win_by_8
        to_home += away_win_by_7
        try:
            away_odds = round((1 - away_win_by_8) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_8) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_8) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(8.0, home_odds, away_odds))

        away_win_by_9 = self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][9] + \
                            self._probability_table_goal_draws[0][1] * self._probability_table_goal_draws[1][10] + \
                            self._probability_table_goal_draws[0][2] * self._probability_table_goal_draws[1][11]
        to_away += away_win_by_9
        to_home += away_win_by_8
        try:
            away_odds = round((1 - away_win_by_9) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_9) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_9) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(9.0, home_odds, away_odds))

        away_win_by_10 = self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][10] + \
                             self._probability_table_goal_draws[0][1] * self._probability_table_goal_draws[1][11]
        to_away += away_win_by_10
        to_home += away_win_by_9
        try:
            away_odds = round((1 - away_win_by_10) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_10) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_10) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(10.0, home_odds, away_odds))

        away_win_by_11 = self._probability_table_goal_draws[0][0] * self._probability_table_goal_draws[1][11]
        to_away += away_win_by_11
        to_home += away_win_by_10
        try:
            away_odds = round((1 - away_win_by_11) / ((1 / self._moneyline.odds_away) - to_away), 3)
        except ZeroDivisionError:
            away_odds = round((1 - away_win_by_11) / consts.AROUND_ZERO, 3) # then closer to 0
        home_odds = round((1 - away_win_by_11) / (1 - (1 / self._moneyline.odds_away) + to_home), 3)
        list_of_handicaps.append(BookmakerHandicap(11.0, home_odds, away_odds))

        list_of_handicaps = sorted(list_of_handicaps, key=lambda bookmaker_handicap: bookmaker_handicap.line)

        # calculate 0.75, 1.25, 1.75, 2.25 ... lines
        i = 1
        asian_lines = []
        for bt in list_of_handicaps:
            try:
                asian_handicap_line = self._get_asian_handicap_line(bt, list_of_handicaps[i])
                asian_lines.append(asian_handicap_line)
                i += 1
            except IndexError:
                break
        list_of_handicaps = sorted(list_of_handicaps + asian_lines,
                                   key=lambda bookmaker_handicap: bookmaker_handicap.line)

        # remove low odds
        list_of_handicaps = BookmakerHandicap.get_only_meaningful_lines(list_of_handicaps)

        # create dict
        dict_handicaps = {}
        for handicap in list_of_handicaps:
            dict_handicaps[handicap.line] = handicap

        return dict_handicaps

    @staticmethod
    def _get_asian_handicap_line(handi_1: BookmakerHandicap, handi_2: BookmakerHandicap) -> BookmakerHandicap:
        """Calculate an Asian handicap by averaging adjacent lines and odds.

        Args:
            handi_1: First neighboring handicap.
            handi_2: Second neighboring handicap.

        Returns:
            Handicap with its line rounded to two decimal places and odds to
            three decimal places.
        """
        line = round((handi_1.line + handi_2.line) / 2, 2)
        home = round((handi_1.odds_home + handi_2.odds_home) / 2, 3)
        away = round((handi_1.odds_away + handi_2.odds_away) / 2, 3)
        return BookmakerHandicap(line, home, away)

    @staticmethod
    def get_opposite_odds(odds: float) -> float:
        """Calculate odds for the complementary outcome.

        Args:
            odds: Probability of the original outcome, despite the name.

        Returns:
            Inverse of the complementary probability, rounded to three
            decimal places. A rounded zero probability is replaced with
            AROUND_ZERO before division.
        """
        opp_probability = round(1.00 - odds, 3)
        if not opp_probability:
            opp_probability = consts.AROUND_ZERO
        return round(1 / opp_probability, 3)

    def print_probability_table_goal_draws(self) -> None:
        """Print home, away, and matching-score probabilities as a grid."""
        table: list[list[str | Probability]] = [
            [' ', *(str(goal) for goal in range(0, 12))],
            ['Home to score', *self.probability_table_goal_draws[0]],
            ['Away to score', *self.probability_table_goal_draws[1]],
            ['Draw cor. score', *self.probability_table_goal_draws[2]],
        ]
        print(tabulate(table, headers='firstrow', tablefmt='grid'))
