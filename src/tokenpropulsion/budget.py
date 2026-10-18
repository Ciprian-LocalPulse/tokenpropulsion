"""Local reservation guards, not a guaranteed provider-side spending cap."""

import math
import threading
from dataclasses import dataclass, field

from .exceptions import InputError


@dataclass
class RequestBudget:
    max_usd: float
    reservation_per_request_usd: float
    max_requests: int = 32
    requests_reserved: int = field(default=0, init=False)
    reserved_usd: float = field(default=0.0, init=False)
    reported_usd: float = field(default=0.0, init=False)
    reported_limit_exceeded: bool = field(default=False, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        if (
            any(
                not math.isfinite(x) or x <= 0
                for x in (self.max_usd, self.reservation_per_request_usd)
            )
            or type(self.max_requests) is not int
            or not 1 <= self.max_requests <= 1000
        ):
            raise InputError("positive finite reservations and request limit [1,1000] required")

    def reserve(self) -> None:
        with self._lock:
            if (
                self.reported_limit_exceeded
                or self.requests_reserved >= self.max_requests
                or self.reserved_usd + self.reservation_per_request_usd > self.max_usd + 1e-12
            ):
                raise InputError("local experiment budget exhausted; no request sent")
            self.requests_reserved += 1
            self.reserved_usd += self.reservation_per_request_usd

    def observe(self, reported_cost: float | None) -> None:
        if reported_cost is not None:
            if not math.isfinite(reported_cost) or reported_cost < 0:
                raise InputError("invalid provider-reported cost")
            with self._lock:
                self.reported_usd += reported_cost
                self.reported_limit_exceeded = self.reported_usd > self.max_usd

    def snapshot(self) -> dict[str, int | float | bool]:
        with self._lock:
            return {
                "max_usd": self.max_usd,
                "requests_reserved": self.requests_reserved,
                "reserved_usd": self.reserved_usd,
                "reported_usd": self.reported_usd,
                "reported_limit_exceeded": self.reported_limit_exceeded,
                "provider_side_hard_cap": False,
            }
