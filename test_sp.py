import sentencepiece as spm

sp = spm.SentencePieceProcessor(model_file="src/services/nws/data/arabic_bpe.model")

text = "شرب الكلب الم"
ids = sp.encode(text, out_type=int)
print(f"Text: {text}")
print(f"IDs: {ids}")
print(f"Pieces: {[sp.id_to_piece(i) for i in ids]}")

# Let's say the next token is 'اء'
next_token_text = "اء"
next_ids = sp.encode(next_token_text, out_type=int)
print(f"Next IDs for 'اء': {next_ids}")
print(f"Next Pieces: {[sp.id_to_piece(i) for i in next_ids]}")

# If we decode the last context ID + the next ID
for next_id in next_ids:
    decoded = sp.decode(ids[-1:] + [next_id])
    print(f"Decoding {ids[-1:]} + [{next_id}] -> '{decoded}'")
    
    # What if we decode the whole context + next id?
    decoded_full = sp.decode(ids + [next_id])
    print(f"Decoding full + [{next_id}] -> '{decoded_full}'")
    print(f"Extracted last word: '{decoded_full.split()[-1]}'")
