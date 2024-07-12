import difflib
import sys
from collections import Counter
from itertools import combinations

sys.path.append("./src/pattern")
from source_preprocessor import variable_name_preprocessing, tokenize_python_code


def compute_token_diff(condition, consequent):
    """トークン化された2つのPythonコード文字列の差分を計算する．

    Args:
        condition (str): 変更前のPythonコード文字列
        consequent (str): 変更後のPythonコード文字列

    Returns:
       list: 差分を示すトークンのリスト．削除されたトークンには「-」、追加されたトークンには「+」が付く．
    """
    token_condition = tokenize_python_code(variable_name_preprocessing(condition))
    token_consequent = tokenize_python_code(variable_name_preprocessing(consequent))
    diff = []

    sm = difflib.SequenceMatcher(None, token_condition, token_consequent)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            for token in token_condition[i1:i2]:
                diff.append(f"-{token}")
            for token in token_consequent[j1:j2]:
                diff.append(f"+{token}")
        elif tag == "delete":
            for token in token_condition[i1:i2]:
                diff.append(f"-{token}")
        elif tag == "insert":
            for token in token_consequent[j1:j2]:
                diff.append(f"+{token}")
        elif tag == "equal":
            for token in token_condition[i1:i2]:
                diff.append(f"={token}")

    return diff


def merge_consecutive_tokens(diff):
    """連続するトークンを結合する．

    Args:
        diff (list): トークンのリスト

    Returns:
        list: 結合されたトークンのリスト
    """
    if not diff:
        return []

    merged_diff = []
    current_token = diff[0]

    for token in diff[1:]:
        if current_token.startswith(('-', '+', '=')) and token.startswith(current_token[0]):
            current_token += token[1:]
            continue
        merged_diff.append(current_token[1:] if current_token.startswith("=") else current_token)
        current_token = token

    merged_diff.append(current_token)
    return merged_diff


def extract_valid_subsequences(tokens):
    """指定された開始トークンで始まり、少なくとも1つの'-'または'+'が含まれる部分列を抽出し、その頻度をカウントする

    Args:
        tokens (list): トークンのリスト

    Returns:
        Counter: 有効な部分列とその頻度を含むカウンターオブジェクト
    """
    subsequences = []
    start_token = tokens[0]
    n = len(tokens)
    for length in range(2, n + 1):  # 部分列の長さを2からnまで変更
        for comb in combinations(range(1, n), length - 1):  # 各長さで部分列を生成（start_tokenを固定）
            subseq = (start_token,) + tuple(tokens[i] for i in comb)
            if any(token.startswith(('-', '+')) for token in subseq):
                subsequences.append(subseq)
    
    # 部分列の頻度をカウント
    subseq_counter = Counter(subsequences)
    
    return subseq_counter


def update_pattern_counter(counter, new_tokens):
    """既存のパターンカウンターに新しいトークンリストから抽出したパターンの頻度を追加する

    Args:
        counter (Counter): 既存のパターンカウンター
        new_tokens (list): 新しいトークンのリスト
    """
    new_subsequences = extract_valid_subsequences(new_tokens)
    counter.update(new_subsequences)


# debag
if __name__ == "__main__":
    # サンプルのトークンリスト
    tokens1 = ['i=dic', '-[', '+.get(', 'STRING', '-]', '+)']
    tokens2 = ['i=dic', '-[', '+.get(', 'STRING', '-]', '+)', '+diff']

    # 最初のトークンリストから有効な部分列を抽出し、その頻度をカウント
    pattern_counter = extract_valid_subsequences(tokens1)

    # 新しいトークンリストからパターンの頻度を更新
    update_pattern_counter(pattern_counter, tokens2)

    # 抽出された有効な部分列とその頻度を表示
    for subseq, count in pattern_counter.items():
        print(f"Pattern: {subseq}, Count: {count}")