# Security policy

The initial 1.0.0 release candidate is maintained on a best-effort community basis;
there is no certification, security audit, support SLA, or guarantee of semantic safety.

Report vulnerabilities privately through GitHub Security Advisories after a repository
is published. Before publication, do not publicly disclose secrets or exploit payloads;
use the repository owner's private contact channel when one is configured.

## Trust and data boundaries

The core is offline, deterministic, and does not execute prompt text. Sensitive syntax
freezes the whole prompt. Validation checks ordered text units, protected identity,
and nonincreasing counts. This does not detect every language or prove equivalence.
Prompts and transformation snapshots exist only in returned in-memory records unless
a caller explicitly exports them. No telemetry, retention, or logging is added by the
core. Optional SDKs and provider infrastructure have independent data policies.

Remote requests require explicit network authorization. Detected sensitive markers need
additional authorization. Detection is heuristic: review all remote datasets yourself.
The xAI key is read from environment and excluded from exception text and repr.
Retries are bounded and may be billable more than once after ambiguous failures.

The FastAPI service requires a configured random bearer token, disables schema/docs,
limits streaming body bytes, and suppresses input-reflecting validation details.
Bind to loopback; public deployment requires TLS, proxy rate/concurrency/time limits,
secret management, and appropriate access-log controls. Avoid browser storage of tokens.
Input limits do not eliminate all denial-of-service risks.

## Supply chain

Actions are pinned to immutable commits; jobs use least privilege. PyPI publishing
requires a protected environment and trusted publishing. Security CI runs Bandit,
package vulnerability auditing, and a bounded repository secret scan. Secret scanning
is heuristic, excludes generated environments/build artifacts, and is not proof that
all possible secrets are absent. Review staged changes before publication.
