"""Verify the declared counted body length without third-party dependencies."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "docs/whitepaper/TokenPropulsion-Whitepaper-v1.0.0rc1.md"
text = path.read_text(encoding="utf-8")
body = text.split("<!-- WORD_COUNT_START -->", 1)[1].split("<!-- WORD_COUNT_END -->", 1)[0]
count = len(re.findall(r"\S+", body))
if count != 10_000:
    raise SystemExit(f"Expected 10000 body words, found {count}")
print(f"Whitepaper verified: {count} body words; front matter and references excluded.")
