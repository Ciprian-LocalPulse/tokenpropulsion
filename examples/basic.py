from tokenpropulsion import compress_prompt

result = compress_prompt("Explain stars.   ")
print(result.optimized_text)
print(result.tokenizer, result.counts_exact)
