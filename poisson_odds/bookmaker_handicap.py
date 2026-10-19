from dataclasses import dataclass

import poisson_odds.consts as consts


@dataclass
class BookmakerHandicap:
    """Represents a bookmaker handicap line and its associated odds.

    Attributes:
        line: Handicap line.
        odds_home: Decimal odds for the home team.
        odds_away: Decimal odds for the away team.
    """

    line: float
    odds_home: float
    odds_away: float

    def __str__(self) -> str:
        """Return the handicap line and its odds as a string."""
        return f"{self.line}: {self.odds_home} / {self.odds_away}"

    def __lt__(self, other: "BookmakerHandicap") -> bool:
        """Compare handicap lines in ascending order."""
        return self.line < other.line

    def __gt__(self, other: "BookmakerHandicap") -> bool:
        """Compare handicap lines in descending order."""
        return self.line > other.line

    @staticmethod
    def get_only_meaningful_lines(
        handicaps: list["BookmakerHandicap"],
    ) -> list["BookmakerHandicap"]:
        """Filter handicap lines by the minimum allowed odds.

        Args:
            handicaps: Handicap lines to filter.

        Returns:
            Handicap lines with both odds meeting the minimum threshold.
        """
        return [
            handicap
            for handicap in handicaps
            if handicap.odds_home >= consts.MIN_ODDS_TO_LINES
            and handicap.odds_away >= consts.MIN_ODDS_TO_LINES
        ]
