# Architecture and decisions

The core uses only the Python standard library. Frozen dataclasses expose original and
optimized text, counts, estimator identity, duration, warnings, stepwise transformation
snapshots, and validation results. `restore()` returns the original without depending on
transformation replay. This trades memory for auditability; a one-megabyte cap bounds
ordinary inputs. Steps can multiply memory by a small profile-dependent constant.

Protection freezes the **whole input** when known risky patterns occur. This avoids
placeholder collisions, trust-boundary crossing, escaping errors, or normalization
inside partly recognized code/structured blocks. Broad false positives are intentional.
Unknown formatting semantics remain a limitation. No natural-language semantic assessor
is installed or implied. The high profile never deletes nonwhitespace units.

Compression profiles are local formatting rules. Validators independently check ordered
nonwhitespace units and protected identity. A failed invariant or increased count returns
original text. Tokenizer failures propagate; unsafe guesses are not substituted.

`Tokenizer` is a protocol, not a dependency on a vendor. The built-in estimator counts
UTF-8 bytes divided by a configured scale and rounds upward. The remote xAI tokenizer
is opt-in and exact for submitted text under the selected provider model; it excludes
chat envelope overhead and does not establish future billing.

CLI imports no web dependencies. The API and SDK load only when explicitly imported.
The xAI adapter sends one user message and never elevates prompt material to a system or
developer message. It retains no conversational history. Provider errors are sanitized.
Benchmark offline reports contain no prompt text. Remote experiments expose only
usage, evaluator decisions, and timings, with sanitized failures.
