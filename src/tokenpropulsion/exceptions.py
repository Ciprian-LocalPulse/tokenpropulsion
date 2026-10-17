"""Stable exceptions whose messages never include prompts or credentials."""


class TokenPropulsionError(Exception):
    """Base public error."""


class InputError(TokenPropulsionError, ValueError):
    """Invalid or oversized input."""


class NetworkDisabledError(TokenPropulsionError):
    """Remote work requires explicit authorization."""


class ProviderError(TokenPropulsionError):
    """A sanitized provider failure."""
