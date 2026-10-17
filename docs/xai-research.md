# xAI integration research

Checked 2026-10-17 against primary sources:

- https://github.com/xai-org/xai-sdk-python
- https://github.com/xai-org/xai-sdk-python/blob/main/examples/sync/tokenizer.py
- https://github.com/xai-org/xai-sdk-python/blob/main/examples/aio/tokenizer.py
- https://docs.x.ai/developers/model-capabilities/text/generate-text
- https://docs.x.ai/developers/advanced-api-usage/async

The official SDK exposes synchronous Client and asynchronous AsyncClient. Chat sampling
uses `client.chat.create`, `chat.append(user(text))`, and `chat.sample()`. SDK source
provides `tokenize.tokenize_text(text, model)` returning a token sequence. It is a
remote API and is not silently used for offline compression. Requests set
`store_messages=False`; timeout is configured on the client. gRPC transient status codes
are used for bounded retries. Usage properties are verified against the installed SDK
in tests; provider success remains unverified without a live request.

No official local tokenizer for every current Grok model was established in this review.
The default estimator is therefore explicitly uncalibrated. No model names or prices are
hardcoded as current. Pricing is caller-supplied with model, source URL, and verification
date. Package and repository naming checks are recorded in docs/validation.md.
