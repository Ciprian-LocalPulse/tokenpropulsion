"""Authenticated, bounded, stateless HTTP API; explicit factory configuration."""

import asyncio
import hmac
import os
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import JSONResponse, Response

from .. import __version__, compress_prompt
from ..exceptions import TokenPropulsionError
from ..security import MAX_INPUT_BYTES


class CompressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(max_length=MAX_INPUT_BYTES)
    level: Literal["low", "medium", "high", "adaptive"] = "medium"


def create_app(*, api_token: str | None = None, requests_per_minute: int = 60) -> FastAPI:
    token = api_token or os.environ.get("TOKENPROPULSION_API_TOKEN")
    if not token or len(token) < 32 or not token.isascii():
        raise ValueError("configure an ASCII API token of at least 32 characters")
    if type(requests_per_minute) is not int or not 1 <= requests_per_minute <= 10000:
        raise ValueError("requests_per_minute must be in [1,10000]")
    arrivals: deque[float] = deque()
    app = FastAPI(
        title="TokenPropulsion",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.middleware("http")
    async def protect(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Apply authorization and streaming byte limits before JSON parsing. No body logs.
        supplied = request.headers.get("authorization", "")
        if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        now = time.monotonic()
        while arrivals and now - arrivals[0] >= 60:
            arrivals.popleft()
        if len(arrivals) >= requests_per_minute:
            return JSONResponse(
                {"detail": "rate limit exceeded"}, status_code=429, headers={"Retry-After": "60"}
            )
        arrivals.append(now)
        if request.headers.get("content-encoding", "identity") != "identity":
            return JSONResponse({"detail": "unsupported encoding"}, status_code=415)
        body = bytearray()

        async def read_body() -> bool:
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_INPUT_BYTES:
                    return False
                body.extend(chunk)
            return True

        try:
            bounded = await asyncio.wait_for(read_body(), timeout=10.0)
        except asyncio.TimeoutError:
            return JSONResponse({"detail": "request timeout"}, status_code=408)
        if not bounded:
            return JSONResponse({"detail": "request too large"}, status_code=413)
        # Starlette Request caches bodies consumed by downstream call_next.
        request._body = bytes(body)
        return await call_next(request)

    @app.exception_handler(RecursionError)
    @app.exception_handler(TokenPropulsionError)
    async def invalid_input(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"detail": "invalid input"}, status_code=422)

    # FastAPI's default validation errors can reflect input. Suppress them.
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": "invalid request"}, status_code=422)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version")
    def version() -> dict[str, str]:
        return {"version": __version__}

    @app.post("/compress")
    @app.post("/analyze")
    def compress(payload: CompressRequest) -> dict[str, Any]:
        return compress_prompt(payload.text, payload.level).to_dict()

    return app
