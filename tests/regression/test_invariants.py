import random
import re

from tokenpropulsion import compress_prompt


def test_seeded_formatting_invariants():
    rng = random.Random(20261017)  # noqa: S311 -- deterministic synthetic fixture generation
    for _ in range(200):
        words = [
            rng.choice(["Stele.", "Explică", "🌍", "never", "```", "value:"])
            for _ in range(rng.randint(0, 30))
        ]
        text = "".join(word + rng.choice([" ", "   ", "\n", "\n\n\n"]) for word in words)
        for level in ["low", "medium", "high"]:
            result = compress_prompt(text, level)
            assert re.findall(r"\S+", text) == re.findall(r"\S+", result.optimized_text)
            assert result.restore() == text
            assert result.optimized_tokens <= result.original_tokens
