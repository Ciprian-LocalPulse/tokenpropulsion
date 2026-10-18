"""Explicit network-only official SDK integration. No credentials in repr or errors."""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

from ..budget import RequestBudget
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
    cached_input_tokens: int | None = None
    reported_cost_usd: float | None = None
    time_to_first_token_seconds: float | None = None


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
    from xai_sdk.cost import cost_usd_from_usage

    cost = cost_usd_from_usage(usage) if hasattr(usage, "HasField") else None
    return ProviderResult(
        response.content,
        int(usage.prompt_tokens),
        int(usage.completion_tokens),
        int(usage.total_tokens),
        time.perf_counter() - start,
        model,
        int(usage.cached_prompt_text_tokens)
        if hasattr(usage, "cached_prompt_text_tokens")
        else None,
        cost,
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
        max_output_tokens: int = 1024,
        temperature: float = 0,
        budget: RequestBudget | None = None,
    ) -> None:
        if (
            not isinstance(model, str)
            or not model
            or not 0 < timeout <= 3600
            or type(max_retries) is not int
            or not 0 <= max_retries <= 3
        ):
            raise InputError("model, timeout (0,3600], and retries [0,3] required")
        if (
            type(max_output_tokens) is not int
            or not 1 <= max_output_tokens <= 8192
            or not 0 <= temperature <= 2
        ):
            raise InputError("output cap [1,8192] and temperature [0,2] required")
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.budget = budget
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
            max_tokens=self.max_output_tokens,
            temperature=self.temperature,
        )
        chat.append(user(text))
        return chat

    def request(self, text: str) -> ProviderResult:
        self._authorize(text)
        start = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            if self.budget is not None:
                self.budget.reserve()
            try:
                with self._client() as client:
                    result = _result(self._chat(client, text).sample(), start, self.model)
                    if self.budget is not None:
                        self.budget.observe(result.reported_cost_usd)
                    return result
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
            if self.budget is not None:
                self.budget.reserve()
            try:
                async with self._client(True) as client:
                    response = await self._chat(client, text).sample()
                    result = _result(response, start, self.model)
                    if self.budget is not None:
                        self.budget.observe(result.reported_cost_usd)
                    return result
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
    count_kind = "provider-exact"

    def __init__(self, adapter: XAIAdapter) -> None:
        self.adapter = adapter
        self.identity = f"xai:remote-text:{adapter.model}"

    def count(self, text: str) -> int:
        return self.adapter.count_tokens(text)
