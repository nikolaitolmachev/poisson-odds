class Probability:
    """Represents a probability with percentage formatting and arithmetic.

    Attributes:
        _probability: Probability value represented as a float.
    """

    def __init__(self, probability: float) -> None:
        self._probability = probability

    @property
    def probability(self) -> float:
        """Return the probability value."""
        return self._probability

    @probability.setter
    def probability(self, value: float) -> None:
        """Set the probability within the valid range.

        Args:
            value: New probability value.

        Raises:
            ValueError: If the value is outside the range [0, 1].
        """
        if not 0 <= value <= 1:
            raise ValueError("Incorrect value of probability!")

        self._probability = value

    def __str__(self) -> str:
        """Return the probability formatted as a percentage."""
        return f"{self._probability:.2%}"

    def __repr__(self) -> str:
        """Return the probability formatted as a percentage."""
        return f"{self._probability:.2%}"

    def __mul__(self, other: "Probability") -> float:
        """Multiply two probabilities, rounded to three decimals."""
        return round(self._probability * other._probability, 3)

    def __add__(self, other: float) -> float:
        """Add a number to the probability, rounded to three decimals."""
        return round(self._probability + other, 3)

    def __sub__(self, other: float) -> float:
        """Subtract a number from the probability, rounded to three decimals."""
        return round(self._probability - other, 3)

    def __radd__(self, other: float) -> float:
        """Support addition with a number on the left."""
        return round(self.__add__(other), 3)
