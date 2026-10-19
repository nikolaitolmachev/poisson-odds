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
            raise ValueError('Incorrect quality value for one of teams at least!')

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
            self._calculate_draw_probability(home_probability, away_probability)
            for home_probability, away_probability in zip(home, away)
        ]
        return [home, away, draws]

    def calculate_total_odds_by_poisson(self) -> dict[float, BookmakerTotal]:
        """Calculate over/under odds from the probability table.

        Returns:
            BookmakerTotal objects keyed by line in ascending order, after
            filtering out lines with odds below the minimum threshold.

        Raises:
            ZeroDivisionError: If an unguarded denominator is zero.
        """
        home, away, draws = self._probability_table_goal_draws
        totals: list[BookmakerTotal] = []
        under = 0.0

        for total_goals in range(12):
            # Early lines have distinct addition and rounding sequences.
            if total_goals == 0:
                under = draws[0].probability
            elif total_goals == 1:
                under = draws[0] + home[1] * away[0] + home[0] * away[1]
            elif total_goals == 2:
                under += draws[1] + home[2] * away[0] + home[0] * away[2]
            elif total_goals == 3:
                under += round(
                    home[2] * away[1] + home[1] * away[2]
                    + home[3] * away[0] + home[0] * away[3],
                    4,
                )
            else:
                midpoint = total_goals // 2
                even_total = total_goals % 2 == 0
                # Keep the Probability seed: its first addition rounds.
                score_probability: Probability | float = draws[midpoint] if even_total else 0
                for home_goals in range(total_goals + 1):
                    if even_total and home_goals == midpoint:
                        continue
                    score_probability += home[home_goals] * away[total_goals - home_goals]
                under += score_probability

            if total_goals < 2 and not under:
                under = consts.AROUND_ZERO
            totals.append(BookmakerTotal(
                total_goals + 0.5,
                Poisson.get_opposite_odds(under),
                round(1 / under, 3),
            ))

        for line in range(1, len(totals)):
            lower, upper = totals[line - 1], totals[line]
            under_odds = round(
                1 / ((1 / lower.odds_under)
                     / (1 / lower.odds_under + 1 / upper.odds_over)),
                3,
            )
            totals.append(BookmakerTotal(line, Poisson.get_opposite_odds(1 / under_odds), under_odds))

        totals = sorted(totals, key=lambda total: total.line)
        asian_totals = [
            self._get_asian_total_line(lower, upper)
            for lower, upper in zip(totals, totals[1:])
        ]
        totals = sorted(totals + asian_totals, key=lambda total: total.line)
        totals = BookmakerTotal.get_only_meaningful_lines(totals)
        return {total.line: total for total in totals}

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

    def calculate_handicap_odds_by_poisson(self) -> dict[float, BookmakerHandicap]:
        """Calculate handicap odds from the probability table.

        Returns:
            BookmakerHandicap objects keyed by line in ascending order, after
            filtering out lines with odds below the minimum threshold.

        Raises:
            ZeroDivisionError: If an unguarded denominator is zero.
        """

        list_of_handicaps: list[BookmakerHandicap] = []

        home_probabilities = self._probability_table_goal_draws[0]
        away_probabilities = self._probability_table_goal_draws[1]

        # Calculate half-integer handicaps from -10.5 to -1.5.
        for margin in range(11, 1, -1):
            home_win_probability = 0.0
            for home_goals in range(margin, 12):
                for away_goals in range(home_goals - margin + 1):
                    home_win_probability += (
                        home_probabilities[home_goals]
                        * away_probabilities[away_goals]
                    )
            if home_win_probability:
                list_of_handicaps.append(BookmakerHandicap(
                    0.5 - margin,
                    round(1 / home_win_probability, 3),
                    Poisson.get_opposite_odds(home_win_probability),
                ))

        # -0.5 = Moneyline home win
        list_of_handicaps.append(
            BookmakerHandicap(
                -0.5,
                self._moneyline.odds_home,
                Poisson.get_opposite_odds(1 / self._moneyline.odds_home),
            )
        )

        # +0
        handicap_0_home_odds = round((1 - (1 / self._moneyline.odds_draw)) / (1 / self._moneyline.odds_home), 3)
        handicap_0_away_odds = round((1 - (1 / self._moneyline.odds_draw)) / (1 / self._moneyline.odds_away), 3)
        list_of_handicaps.append(BookmakerHandicap(0, handicap_0_home_odds, handicap_0_away_odds))

        # +0.5 = Moneyline away win
        list_of_handicaps.append(
            BookmakerHandicap(0.5, Poisson.get_opposite_odds(1 / self._moneyline.odds_away), self._moneyline.odds_away)
        )

        # Calculate half-integer handicaps from +1.5 to +10.5.
        for margin in range(2, 12):
            away_win_probability = 0.0
            for home_goals in range(12 - margin):
                for away_goals in range(home_goals + margin, 12):
                    away_win_probability += (
                        home_probabilities[home_goals]
                        * away_probabilities[away_goals]
                    )
            if away_win_probability:
                list_of_handicaps.append(BookmakerHandicap(
                    margin - 0.5,
                    Poisson.get_opposite_odds(away_win_probability),
                    round(1 / away_win_probability, 3),
                ))

        # Calculate integer handicaps from -1.0 to -11.0.
        list_of_handicaps.extend(self._calculate_integer_handicap_lines(
            range(-1, -12, -1), self._moneyline.odds_home,
        ))
        # Calculate integer handicaps from +1.0 to +11.0.
        list_of_handicaps.extend(self._calculate_integer_handicap_lines(
            range(1, 12), self._moneyline.odds_away,
        ))

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

    def _calculate_integer_handicap_lines(
        self, lines: range, moneyline_odds: float,
    ) -> list[BookmakerHandicap]:
        """Calculate integer handicaps for one side in margin order.

        Args:
            lines: Same-sign lines ordered by increasing absolute value.
            moneyline_odds: Home win odds for negative lines, away win odds
                for positive lines.

        Returns:
            Handicap objects in the supplied line order.

        Raises:
            ZeroDivisionError: If an unguarded denominator is zero.
        """
        home = self._probability_table_goal_draws[0]
        away = self._probability_table_goal_draws[1]
        handicaps: list[BookmakerHandicap] = []
        to_winner = to_other = previous_probability = 0.0
        for line in lines:
            margin = abs(line)
            probability = 0.0
            for home_goals in range(max(0, -line), min(12, 12 - line)):
                probability += home[home_goals] * away[home_goals + line]
            if margin == 1:
                to_winner = probability
            else:
                to_winner += probability
                if margin == 2:
                    to_other = previous_probability
                else:
                    to_other += previous_probability
            try:
                winner_odds = round(
                    (1 - probability)
                    / ((1 / moneyline_odds) - to_winner), 3,
                )
            except ZeroDivisionError:
                winner_odds = round((1 - probability) / consts.AROUND_ZERO, 3)
            if margin == 1:
                other_odds = round((1 - probability) / (1 - (1 / moneyline_odds)), 3)
            else:
                other_odds = round((1 - probability) / (1 - (1 / moneyline_odds) + to_other), 3)
            home_odds, away_odds = (
                (winner_odds, other_odds) if line < 0
                else (other_odds, winner_odds)
            )
            handicaps.append(BookmakerHandicap(float(line), home_odds, away_odds))
            previous_probability = probability
        return handicaps

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
