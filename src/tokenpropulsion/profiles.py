"""Profiles change formatting only; none deletes words or repeated instructions."""

from dataclasses import dataclass

from .exceptions import InputError


@dataclass(frozen=True)
class Profile:
    collapse_blank_lines: bool
    collapse_spaces: bool


PROFILES = {
    "low": Profile(False, False),
    "medium": Profile(True, False),
    "high": Profile(True, True),
}


def get_profile(level: str) -> Profile:
    if level not in PROFILES:
        raise InputError("level must be low, medium, or high")
    return PROFILES[level]
