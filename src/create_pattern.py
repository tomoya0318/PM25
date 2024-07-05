import json
import difflib
from collections import Counter

def extract_code_chunks(json_data):
    """Extract pairs of code chunks from JSON data."""
    chunks = [(item['condition'], item['consequent']) for item in json_data]
    return chunks

def tokenize_and_normalize(chunk):
    """Divide and normalize tokens."""
    tokens = chunk.replace('(', ' ( ').replace(')', ' ) ').split()
    normalized_tokens = []
    for token in tokens:
        if token.isidentifier():
            normalized_tokens.append('IDENTIFIER')
        elif token.isdigit():
            normalized_tokens.append('NUMBER')
        elif token.startswith('"') and token.endswith('"'):
            normalized_tokens.append('STRING')
        else:
            normalized_tokens.append(token)
    return normalized_tokens

def line_diff_to_token_diff(old_tokens, new_tokens):
    """Convert line difference to token difference sequence."""
    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)
    diffs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            diffs.append(('-', old_tokens[i1:i2], new_tokens[j1:j2]))
        elif tag == 'delete':
            diffs.append(('-', old_tokens[i1:i2], []))
        elif tag == 'insert':
            diffs.append(('+', [], new_tokens[j1:j2]))
    return diffs

def extract_token_diff_patterns(diffs):
    """Extract token difference sequence pattern."""
    patterns = []
    for sign, old_tokens, new_tokens in diffs:
        pattern = [f'{sign}{token}' for token in old_tokens] + [f'+{token}' for token in new_tokens]
        patterns.append(pattern)
    return patterns

def count_patterns(patterns):
    """Count each pattern's appeared time from other patches."""
    pattern_counts = Counter()
    for pattern in patterns:
        pattern_counts.update([' '.join(pattern)])
    return pattern_counts

def process_json_data(json_data):
    """Process JSON data to extract and count token difference patterns."""
    chunks = extract_code_chunks(json_data)
    patterns = []
    for old_chunk, new_chunk in chunks:
        old_tokens = tokenize_and_normalize(' '.join(old_chunk))
        new_tokens = tokenize_and_normalize(' '.join(new_chunk))
        diffs = line_diff_to_token_diff(old_tokens, new_tokens)
        chunk_patterns = extract_token_diff_patterns(diffs)
        patterns.extend(chunk_patterns)
    return count_patterns(patterns)

# JSONファイルを読み込む
with open('input.json', 'r', encoding='utf-8') as file:
    json_data = json.load(file)

pattern_counts = process_json_data(json_data)
for pattern, count in pattern_counts.items():
    print(f'Pattern: {pattern}, Count: {count}')
