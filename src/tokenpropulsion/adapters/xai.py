"""Explicit network-only official SDK integration. No credentials in repr or errors."""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

from ..compressor import compress_prompt
from ..exceptions import InputError, ProviderError
from ..security import authorize_network


@dataclass(frozen=True)
class ProviderResult:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    remote_seconds: float
    model: str


def _retryable(error: Exception) -> bool:
    code = getattr(error, "code", None)
    if callable(code):
        return getattr(code(), "name", "") in {
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
            "DEADLINE_EXCEEDED",
            "INTERNAL",
        }
    return False


def _result(response: Any, start: float, model: str) -> ProviderResult:
    usage = response.usage
    return ProviderResult(
        response.content,
        int(usage.prompt_tokens),
        int(usage.completion_tokens),
        int(usage.total_tokens),
        time.perf_counter() - start,
        model,
    )


class XAIAdapter:
    """Creating this adapter does not contact xAI. Requests need allow_network=True.

    max_retries counts retries after the initial attempt. Retrying inference can incur
    duplicate charges if a response was lost. Keep retries at zero when this matters.
    """

    def __init__(
        self,
        model: str,
        *,
        allow_network: bool = False,
        allow_sensitive: bool = False,
        timeout: float = 60,
        max_retries: int = 0,
    ) -> None:
        if (
            not isinstance(model, str)
            or not model
            or not 0 < timeout <= 3600
            or type(max_retries) is not int
            or not 0 <= max_retries <= 3
        ):
            raise InputError("model, timeout (0,3600], and retries [0,3] required")
        self.model = model
        self.allow_network = allow_network
        self.allow_sensitive = allow_sensitive
        self.timeout = timeout
        self.max_retries = max_retries

    def _authorize(self, text: str) -> None:
        authorize_network(self.allow_network, text, self.allow_sensitive)
        if not os.environ.get("XAI_API_KEY"):
            raise ProviderError("XAI_API_KEY is required")

    def _client(self, asynchronous: bool = False) -> Any:
        try:
            from xai_sdk import AsyncClient, Client
        except ImportError:
            raise ProviderError("install tokenpropulsion[xai] to use xAI") from None
        factory = AsyncClient if asynchronous else Client
        return factory(api_key=os.environ["XAI_API_KEY"], timeout=self.timeout)

    def _chat(self, client: Any, text: str) -> Any:
        from xai_sdk.chat import user

        chat = client.chat.create(
            model=self.model,
            store_messages=False,
            max_tokens=1024,
            temperature=0,
        )
        chat.append(user(text))
        return chat

    def request(self, text: str) -> ProviderResult:
        self._authorize(text)
        start = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            try:
                with self._client() as client:
                    return _result(self._chat(client, text).sample(), start, self.model)
            except Exception as error:
                if attempt < self.max_retries and _retryable(error):
                    time.sleep(min(2**attempt, 4))
                else:
                    raise ProviderError("xAI request failed; provider details suppressed") from None
        raise ProviderError("retry budget exhausted")  # pragma: no cover

    async def arequest(self, text: str) -> ProviderResult:
        self._authorize(text)
        start = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            try:
                async with self._client(True) as client:
                    response = await self._chat(client, text).sample()
                    return _result(response, start, self.model)
            except Exception as error:
                if attempt < self.max_retries and _retryable(error):
                    await asyncio.sleep(min(2**attempt, 4))
                else:
                    raise ProviderError("xAI request failed; provider details suppressed") from None
        raise ProviderError("retry budget exhausted")  # pragma: no cover

    def compare(self, text: str, level: str = "medium") -> dict[str, Any]:
        self._authorize(text)
        compressed = compress_prompt(text, level)
        # Both calls use identical model and generation parameters.
        return {
            "compression": compressed,
            "original": self.request(text),
            "optimized": self.request(compressed.optimized_text),
        }

    def count_tokens(self, text: str) -> int:
        self._authorize(text)
        for attempt in range(self.max_retries + 1):
            try:
                with self._client() as client:
                    return len(client.tokenize.tokenize_text(text, model=self.model))
            except Exception as error:
                if attempt < self.max_retries and _retryable(error):
                    time.sleep(min(2**attempt, 4))
                else:
                    raise ProviderError("xAI tokenization failed; details suppressed") from None
        raise ProviderError("retry budget exhausted")  # pragma: no cover


class XAITokenizer:
    """Exact provider text tokenization; excludes chat envelope and hidden overhead.

    This tokenizer makes network requests on each count; do not pass it to a local
    compression benchmark, which measures CPU processing separately from network.
    """

    exact = True

    def __init__(self, adapter: XAIAdapter) -> None:
        self.adapter = adapter
        self.identity = f"xai:remote-text:{adapter.model}"

    def count(self, text: str) -> int:
        return self.adapter.count_tokens(text)
