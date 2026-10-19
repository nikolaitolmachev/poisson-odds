from dataclasses import dataclass

import poisson_odds.consts as consts


@dataclass
class BookmakerTotal:
    """Represents a bookmaker total line and its associated odds.

    Attributes:
        line: Total line.
        odds_over: Decimal odds for the Over outcome.
        odds_under: Decimal odds for the Under outcome.
    """

    line: float
    odds_over: float
    odds_under: float

    def __str__(self) -> str:
        """Return the total line and its odds as a string."""
        return f"Over/Under {self.line}: {self.odds_over} / {self.odds_under}"

    def __lt__(self, other: "BookmakerTotal") -> bool:
        """Compare total lines in ascending order."""
        return self.line < other.line

    def __gt__(self, other: "BookmakerTotal") -> bool:
        """Compare total lines in descending order."""
        return self.line > other.line

    @staticmethod
    def get_only_meaningful_lines(
        totals: list["BookmakerTotal"],
    ) -> list["BookmakerTotal"]:
        """Filter total lines by the minimum allowed odds.

        Args:
            totals: Total lines to filter.

        Returns:
            Total lines with both odds meeting the minimum threshold.
        """
        return [
            total
            for total in totals
            if total.odds_over >= consts.MIN_ODDS_TO_LINES
            and total.odds_under >= consts.MIN_ODDS_TO_LINES
        ]
