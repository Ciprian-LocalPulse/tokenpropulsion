# Research, migration and experimental boundaries

Version 2.0.0a1 retains `compress_prompt(text, level, tokenizer=...)`, existing result
fields and the old flat CLI. New result metadata has defaults; `saved_percent` is an
alias. Explicit strategies and structured documents are opt-in. The HTTP API permits
adaptive formatting but does not accept executable validators or local model paths.

## Research basis and licensing

LLMLingua studies learned prompt pruning, while LLMLingua-2 uses distilled token
classification. They motivate evaluating task quality separately from compression
ratio. Neither implementation was copied, installed or benchmarked here; no superiority
claim is supported. Microsoft's implementation is MIT licensed; specific model weights
require their own license review.

- Jiang et al., LLMLingua (EMNLP 2023): https://aclanthology.org/2023.emnlp-main.825/
- Pan et al., LLMLingua-2 (Findings ACL 2024): https://aclanthology.org/2024.findings-acl.57/
- Microsoft license: https://github.com/microsoft/LLMLingua/blob/main/LICENSE
- SentenceTransformer local loading: https://www.sbert.net/docs/package_reference/sentence_transformer/model.html
- SentenceTransformers Apache-2.0 license: https://github.com/huggingface/sentence-transformers/blob/main/LICENSE
- Official xAI generation reference: https://docs.x.ai/developers/model-capabilities/text/generate-text
- Official SDK tokenizer: https://github.com/xai-org/xai-sdk-python/blob/main/src/xai_sdk/sync/tokenizer.py

The optional embedding backend requires an existing local directory and disables
remote code and network loading. Safetensors is requested. Its dependency is isolated
in the semantic extra. No weights or heavy dependencies are bundled, no model was
loaded in release evaluation, and only a deterministic model stub exercises the adapter.
Review weights, configuration, provenance, resource costs and license before adoption.

## Strategy contracts

Structural paragraph deduplication requires a caller-provided task validator.
Lexical substitutions cover only four phrases; they do not constitute a general
semantic compressor. The default fallback returns original input when proposal,
validation, preservation or token-count checks fail. A caller accepting every candidate
can defeat task correctness; such a validator is outside the tested contracts.

Structured documents preserve instructions and question exactly, serialize untrusted
contexts as JSON, retain source and trust labels, and remove only exact earlier duplicates
explicitly declared idempotent. This models a set-like retrieval contract, not arbitrary
RAG correctness or resistance to every prompt injection.

Reversible zlib/base64 encoding is transport compression. Count the entire decoder and
envelope overhead using `wire_accounting`; a language model is not assumed able to decode
it. Decoding enforces the 1 MB limit and rejects malformed/trailing streams.

## Running studies responsibly

Local experiments disclose tokenizer provenance and do not send prompts remotely.
Tiktoken is exact only for its chosen vocabulary. A compatible-local classification
requires external versioned compatibility evidence; this release supplies no such Grok
artifact. Provider-exact tokenization is a separate authorized network operation.

The xAI CLI study requires billing/network flags, a model, RequestBudget, worst-case
retry reservations and expected outputs. Entire task contracts and optimized prompts
are preflighted before any request. Quality acceptance requires every optimized answer
to pass the declared evaluator and no failed pair. This is a small-study gate, not a
statistical equivalence test. Provider usage/cost is distinct from invoice billing.
A reservation is an estimate; real costs can exceed it. Configure a provider-side cap.

No live study was executed because no key/model budget was supplied. TTFT/streaming,
invoice reconciliation, independent real-world corpus validation, loaded-model quality,
LLMLingua execution and production scalability remain pending.
