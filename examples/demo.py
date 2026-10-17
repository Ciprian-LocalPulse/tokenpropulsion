"""Reproducible terminal demo. Generates real results, no canned savings."""

from tokenpropulsion import compress_prompt

for prompt in ["Explain stars.\n\n\nUse simple language.", 'Return JSON: {"ok":true}  ']:
    result = compress_prompt(prompt)
    print("Input:", repr(prompt))
    print("Output:", repr(result.optimized_text))
    print("Tokenizer:", result.tokenizer, "exact:", result.counts_exact)
    print("Estimated savings %:", round(result.tokens_saved_percent, 2))
    print("Semantic equivalence assessed:", result.semantic_equivalence_assessed)
