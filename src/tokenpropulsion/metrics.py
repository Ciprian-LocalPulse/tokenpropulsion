"""No built-in prices. Users supply dated and sourced input-token pricing."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Pricing:
    model: str
    input_per_million: float
    currency: str
    source_url: str
    verified_on: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.input_per_million) or self.input_per_million < 0:
            raise ValueError("price must be finite and nonnegative")
        if not all((self.model, self.currency, self.source_url, self.verified_on)):
            raise ValueError("pricing requires model, currency, source, and verification date")

    def input_difference(self, original: int, optimized: int) -> float:
        if min(original, optimized) < 0:
            raise ValueError("token counts must be nonnegative")
        return (original - optimized) * self.input_per_million / 1_000_000


def percentile(values: list[float], quantile: float) -> float:
    if not values or not 0 <= quantile <= 1:
        raise ValueError("nonempty values and a quantile in [0, 1] required")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
