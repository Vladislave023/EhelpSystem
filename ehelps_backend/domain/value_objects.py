from __future__ import annotations

from dataclasses import dataclass
import math
import re


RANGE_PATTERN = re.compile(
    r"^(?P<kind>[IR])\[(?P<lower>-?\d+(?:\.\d+)?);(?P<upper>-?\d+(?:\.\d+)?)\]$"
)


@dataclass(frozen=True, slots=True)
class ValueRange:
    kind: str
    lower: float
    upper: float

    @classmethod
    def from_expression(cls, expression: str) -> "ValueRange":
        normalized = expression.replace(" ", "")
        match = RANGE_PATTERN.match(normalized)
        if match is None:
            raise ValueError(f"Некорректный формат диапазона: {expression}")

        kind = match.group("kind")
        lower = float(match.group("lower"))
        upper = float(match.group("upper"))

        if lower > upper:
            raise ValueError(f"Нижняя граница больше верхней: {expression}")

        return cls(kind=kind, lower=lower, upper=upper)

    def contains(self, value: float) -> bool:
        numeric_value = float(value)

        if self.kind == "I" and not math.isclose(numeric_value, round(numeric_value)):
            return False

        return self.lower <= numeric_value <= self.upper

    def contains_range(self, other: "ValueRange") -> bool:
        if self.kind != other.kind:
            return False
        return self.lower <= other.lower and other.upper <= self.upper

    def __str__(self) -> str:
        return f"{self.kind}[{self._format_number(self.lower)};{self._format_number(self.upper)}]"

    @staticmethod
    def _format_number(value: float) -> str:
        if math.isclose(value, round(value)):
            return str(int(round(value)))
        return f"{value:g}"
