"""Tokenizer for the Word N-Gram model.

Isolates punctuation and injects sentence boundaries (<s>, </s>).
"""

import re
from src.core.utils.arabic import normalize_arabic_surface

SENTENCE_END = {'.', '!', '?', '؟'}
KEEP_AS_TOKEN = {',', '،', ':', ';', '؛', '"', "'", '-'}

# Regex to isolate mid-sentence punctuation and sentence end punctuation
# It wraps these characters in spaces so text.split() will treat them as standalone tokens
PUNCT_SPLIT_RE = re.compile(r'([.!؟?,،:;؛"\'-])')

def tokenize_text(text: str, is_inference: bool = False) -> list[str]:
    """Normalize and tokenize text into words and punctuation marks.
    
    Automatically injects <s> and </s> at sentence boundaries.
    If is_inference is True, it will not forcefully close the sentence with </s>
    if the sentence is incomplete, allowing NWP to predict the next word.
    """
    # 1. Normalize arabic characters
    text = normalize_arabic_surface(text)
    
    # 2. Add spaces around all punctuation so we can split by whitespace
    text = PUNCT_SPLIT_RE.sub(r' \1 ', text)
    
    # 3. Tokenize and inject sentence boundaries
    tokens = ['<s>']
    
    for token in text.split():
        if token in SENTENCE_END:
            # When we hit a period or question mark, the sentence ends and a new one begins
            tokens.append('</s>')
            tokens.append('<s>')
        elif token in KEEP_AS_TOKEN:
            # Mid-sentence punctuation is kept as a token
            tokens.append(token)
        else:
            if token.strip():
                tokens.append(token)
            
    # If the text didn't end with a punctuation mark, manually close the sentence
    # UNLESS we are doing inference, where the user is currently typing an incomplete sentence!
    if not is_inference and tokens[-1] != '</s>':
        tokens.append('</s>')
        
    # Clean up empty sentence blocks (e.g. if the text was just punctuation)
    # We remove cases where <s> is immediately followed by </s>
    cleaned_tokens = []
    skip_next = False
    for i in range(len(tokens) - 1):
        if skip_next:
            skip_next = False
            continue
            
        if tokens[i] == '<s>' and tokens[i+1] == '</s>':
            skip_next = True
        else:
            cleaned_tokens.append(tokens[i])
            
    if not skip_next:
        cleaned_tokens.append(tokens[-1])
        
    return cleaned_tokens
