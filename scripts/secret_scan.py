"""Bounded high-confidence secret scan. Does not print matched credentials.

This is not a substitute for a dedicated secret scanner or human review.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
}
PATTERNS = [
    re.compile(r"gh[pousr]_" + r"[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_" + r"[A-Za-z0-9_]{60,}"),
    re.compile(r"(?:xai-|sk-)" + r"[A-Za-z0-9_-]{32,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+" + r"[A-Za-z0-9+/=]{40,}"),
]


def main() -> int:
    failures = []
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or SKIP.intersection(path.relative_to(ROOT).parts):
            continue
        if path.stat().st_size > 2_000_000 or path.suffix in {".png", ".jpg", ".zip", ".gz"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        checked += 1
        if any(pattern.search(text) for pattern in PATTERNS):
            failures.append(str(path.relative_to(ROOT)))
    for name in failures:
        print(f"Possible secret in: {name}")
    print(f"Scanned {checked} text files; {len(failures)} high-confidence findings.")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
