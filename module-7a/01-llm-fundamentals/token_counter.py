import tiktoken

encoder = tiktoken.encoding_for_model("gpt-5.6")

texts = [
    "The patient should take 500mg of ibuprofen twice daily",
    "Explain transformer architecture in detail",
    "What is the meaning of life?"
]

for text in texts:
    tokens = encoder.encode(text)
    print(f"1. Text: {text}")
    print(f"2. Token count: {len(tokens)}")
    print(f"3. Tokens: {tokens}")
    print("4. Decoding Tokens...")
    for token in tokens:
        print(f"    - Token {token}: {encoder.decode([token])}")
    print("\n")