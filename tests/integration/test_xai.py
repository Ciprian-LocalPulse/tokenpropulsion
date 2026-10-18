import asyncio
import builtins
import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest
import xai_sdk
from xai_sdk.proto import usage_pb2

from tokenpropulsion.adapters.xai import XAIAdapter, XAITokenizer, _retryable
from tokenpropulsion.exceptions import InputError, NetworkDisabledError, ProviderError


@pytest.fixture
def sdk(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "EXAMPLE_TEST_KEY")
    response = SimpleNamespace(
        content="OK",
        usage=usage_pb2.SamplingUsage(prompt_tokens=12, completion_tokens=3, total_tokens=15),
    )
    sync = MagicMock()
    sync.__enter__.return_value = sync
    sync.chat.create.return_value.sample.return_value = response
    sync.tokenize.tokenize_text.return_value = [1, 2, 3]
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=async_client)
    async_client.__aexit__ = AsyncMock(return_value=False)
    async_client.chat.create.return_value.sample = AsyncMock(return_value=response)
    sync_factory, async_factory = MagicMock(return_value=sync), MagicMock(return_value=async_client)
    monkeypatch.setattr(xai_sdk, "Client", sync_factory)
    monkeypatch.setattr(xai_sdk, "AsyncClient", async_factory)
    monkeypatch.setattr("tokenpropulsion.adapters.xai.time.sleep", lambda seconds: None)
    monkeypatch.setattr("tokenpropulsion.adapters.xai.asyncio.sleep", AsyncMock())
    return sync, async_client, sync_factory, async_factory


def test_sync_compare_and_tokenizer(sdk):
    sync, _, factory, _ = sdk
    adapter = XAIAdapter("fake", allow_network=True, timeout=42)
    result = adapter.request("Hello.")
    assert (result.input_tokens, result.output_tokens, result.total_tokens) == (12, 3, 15)
    assert result.content == "OK"
    assert result.remote_seconds >= 0
    assert adapter.compare("Hello.   ")["optimized"].content == "OK"
    assert XAITokenizer(adapter).count("Hello.") == 3
    assert XAITokenizer(adapter).identity == "xai:remote-text:fake"
    factory.assert_called_with(api_key="EXAMPLE_TEST_KEY", timeout=42)
    kwargs = sync.chat.create.call_args.kwargs
    assert kwargs["store_messages"] is False
    assert kwargs["model"] == "fake"
    assert sync.chat.create.return_value.append.called
    assert "EXAMPLE_TEST_KEY" not in repr(adapter)


def test_async(sdk):
    _, asynchronous, _, factory = sdk
    result = asyncio.run(XAIAdapter("fake", allow_network=True).arequest("Hello."))
    assert result.content == "OK"
    assert asynchronous.chat.create.return_value.sample.await_count == 1
    assert factory.called


def test_sync_and_async_budget_blocks_before_extra_request(sdk):
    from tokenpropulsion.budget import RequestBudget

    sync, asynchronous, _, _ = sdk
    usage = sync.chat.create.return_value.sample.return_value.usage
    usage.cost_in_usd_ticks = 10_000_000
    usage.cached_prompt_text_tokens = 2
    budget = RequestBudget(0.02, 0.01, 2)
    adapter = XAIAdapter("fake", allow_network=True, budget=budget)
    result = adapter.request("Hello.")
    assert result.content == "OK" and result.cached_input_tokens == 2
    assert result.reported_cost_usd == pytest.approx(0.001)
    assert asyncio.run(adapter.arequest("Hello.")).content == "OK"
    with pytest.raises(InputError, match="budget exhausted"):
        adapter.request("Hello.")
    assert sync.chat.create.return_value.sample.call_count == 1
    assert asynchronous.chat.create.return_value.sample.await_count == 1
    assert budget.snapshot()["requests_reserved"] == 2
    assert budget.snapshot()["reported_usd"] == pytest.approx(0.002)


def test_opt_in_and_configuration(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(NetworkDisabledError):
        XAIAdapter("fake").request("Hello.")
    with pytest.raises(NetworkDisabledError):
        XAIAdapter("fake").compare("Hello.")
    with pytest.raises(ProviderError, match="XAI_API_KEY"):
        XAIAdapter("fake", allow_network=True).request("Hello.")
    with pytest.raises(NetworkDisabledError):
        XAIAdapter("fake", allow_network=True).request("password=EXAMPLE")
    for kwargs in [
        {"model": ""},
        {"model": "x", "timeout": 0},
        {"model": "x", "timeout": float("nan")},
        {"model": "x", "max_retries": 4},
        {"model": "x", "max_retries": 1.5},
    ]:
        with pytest.raises(InputError):
            XAIAdapter(**kwargs)


class Transient(Exception):
    def code(self):
        return grpc.StatusCode.RESOURCE_EXHAUSTED


def test_bounded_retry_and_sanitization(sdk):
    sync, asynchronous, _, _ = sdk
    response = sync.chat.create.return_value.sample.return_value
    sync.chat.create.return_value.sample.side_effect = [Transient("PRIVATE"), response]
    adapter = XAIAdapter("fake", allow_network=True, max_retries=1)
    assert adapter.request("Hello.").content == "OK"
    assert sync.chat.create.return_value.sample.call_count == 2
    asynchronous.chat.create.return_value.sample.side_effect = [Transient("PRIVATE"), response]
    assert asyncio.run(adapter.arequest("Hello.")).content == "OK"
    sync.tokenize.tokenize_text.side_effect = [Transient("PRIVATE"), [1]]
    assert adapter.count_tokens("Hello.") == 1
    sync.chat.create.return_value.sample.side_effect = Transient("PRIVATE")
    with pytest.raises(ProviderError) as caught:
        adapter.request("Hello.")
    assert "PRIVATE" not in str(caught.value)
    assert caught.value.__suppress_context__
    assert sync.chat.create.return_value.sample.call_count == 4
    asynchronous.chat.create.return_value.sample.side_effect = RuntimeError("PRIVATE")
    with pytest.raises(ProviderError):
        asyncio.run(adapter.arequest("Hello."))
    sync.tokenize.tokenize_text.side_effect = RuntimeError("PRIVATE")
    with pytest.raises(ProviderError):
        adapter.count_tokens("Hello.")
    assert not _retryable(RuntimeError())
    assert _retryable(Transient())


def test_missing_optional_sdk(monkeypatch):
    adapter = XAIAdapter("fake")
    original = builtins.__import__

    def no_sdk(name, *args, **kwargs):
        if name == "xai_sdk":
            raise ImportError
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_sdk)
    with pytest.raises(ProviderError, match="install"):
        adapter._client()


def test_installed_official_sdk_contract():
    # Inspect real SDK signatures and protobuf usage without constructing a network client.
    from xai_sdk.aio.chat import Client as AsyncChat
    from xai_sdk.sync.chat import Client as SyncChat
    from xai_sdk.sync.tokenizer import Client as Tokenizer

    for client in [xai_sdk.Client, xai_sdk.AsyncClient]:
        assert "timeout" in inspect.signature(client).parameters
    for chat in [SyncChat, AsyncChat]:
        signature = inspect.signature(chat.create)
        for parameter in ["model", "store_messages", "max_tokens", "temperature"]:
            assert parameter in signature.parameters
    assert "model" in inspect.signature(Tokenizer.tokenize_text).parameters
    fields = usage_pb2.SamplingUsage.DESCRIPTOR.fields_by_name
    assert {"prompt_tokens", "completion_tokens", "total_tokens"} <= set(fields)
