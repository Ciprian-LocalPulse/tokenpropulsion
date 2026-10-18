"""Provider-neutral response and request interfaces. No provider SDK imports."""

from typing import Protocol


class UsageResponse(Protocol):
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    remote_seconds: float
    model: str


class Provider(Protocol):
    model: str

    def request(self, text: str) -> UsageResponse: ...

    async def arequest(self, text: str) -> UsageResponse: ...
