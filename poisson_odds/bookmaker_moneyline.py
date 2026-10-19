from dataclasses import dataclass


@dataclass
class BookmakerMoneyline:
    """Represents a bookmaker moneyline (1-X-2) and its associated odds.

    Attributes:
        odds_home: Decimal odds for the home team to win.
        odds_draw: Decimal odds for a draw.
        odds_away: Decimal odds for the away team to win.
    """

    odds_home: float
    odds_draw: float
    odds_away: float

    def __str__(self) -> str:
        """Return the moneyline odds as a string."""
        return f"1-X-2: {self.odds_home}-{self.odds_draw}-{self.odds_away}"
