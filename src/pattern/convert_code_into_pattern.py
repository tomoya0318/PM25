import difflib
from collections import Counter
from itertools import combinations
import tokenize
from pattern.source_preprocessor import variable_name_preprocessing, tokenize_python_code


def compute_token_diff(condition, consequent):
    """トークン化された2つのPythonコード文字列の差分を計算する．

    Args:
        condition (str): 変更前のPythonコード文字列
        consequent (str): 変更後のPythonコード文字列

    Returns:
       list: 差分を示すトークンのリスト．削除されたトークンには「-」、追加されたトークンには「+」が付く．
    """
    try:
        token_condition = tokenize_python_code(variable_name_preprocessing(condition))
        token_consequent = tokenize_python_code(variable_name_preprocessing(consequent))
    except tokenize.TokenError:
        return []

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
        if current_token.startswith(("-", "+", "=")) and token.startswith(current_token[0]):
            current_token += token[1:]
            continue
        merged_diff.append(current_token)
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
            if any(token.startswith(("-", "+")) for token in subseq):
                subsequences.append(subseq)

    # 部分列の頻度をカウント
    subseq_counter = Counter(subsequences)

    return subseq_counter


def extract_trigger_sequence(pattern):
    """パターンからトリガーシーケンスを抽出する．

    Args:
        pattern (tuple): パターンのトークンシーケンス

    Returns:
        tuple: トリガーシーケンスのトークンシーケンス
    """
    trigger_sequence = tuple(token for token in pattern if token.startswith("=") or token.startswith("-"))
    return trigger_sequence


def update_pattern_counter(counter, new_tokens):
    """既存のパターンカウンターに新しいトークンリストから抽出したパターンの頻度を追加する

    Args:
        counter (Counter): 既存のパターンカウンター
        new_tokens (list): 新しいトークンのリスト
    """
    new_subsequences = extract_valid_subsequences(new_tokens)
    counter.update(new_subsequences)


def _remove_equals(token):
    """トークンの最初の=だけを削除

    Args:
        token (string): =が含まれているかを確認するトークン

    Returns:
        string: =を排除したトークン
    """
    if token.startswith("="):
        return token[1:]
    return token


def filter_patterns(counter, triggerable_initial, actually_changed, threshold=0.1):
    """パターンカウンターから指定された条件を満たさないパターンをフィルタリングする
        条件
        - 変更を提案しないコードの削除
        - 意味が重複するパターンの削除
        - 10%未満の信頼度のパターンを削除
        - 1度しか出現していないパターンを削除

    Args:
        counter (Counter): パターンカウンター
        triggerable_initial (Counter): トリガーシーケンスが含まれる初期パッチのカウンター
        actually_changed (Counter): 実際に変更された統合パッチのカウンター
        threshold (float): 信頼度の閾値

    Returns:
        Counter: フィルタリングされたパターンカウンター
    """
    filtered_counter = Counter()
    seen_patterns = set()

    # アイテムを長さの降順にソートして，反復処理
    # アイテムを長さの降順にソートして，反復処理
    for pattern, count in sorted(counter.items(), key=lambda x: -len(x[0])):
        # 1度しか出現していないパターンを削除
        if count <= 1:
            continue
        # 変更を提案しないコード（削除のみまたは削除と変更なしのみ）を削除
        if all(token.startswith("-") or token.startswith("=") for token in pattern):
            continue

        # トリガーシーケンスを抽出
        trigger_sequence = extract_trigger_sequence(pattern)
        # 信頼度を計算
        confidence = (
            actually_changed[pattern] / triggerable_initial[trigger_sequence]
            if triggerable_initial[trigger_sequence] > 0
            else 0
        )

        # 10%未満の信頼度のパターンを削除
        if confidence < threshold:
            continue

        # トークンから`=`を削除したパターンを作成
        pattern_without_equals = tuple(_remove_equals(token) for token in pattern)

        # 同じトークンが含まれる大きいパターンを優先
        if not any(set(pattern_without_equals).issubset(set(seen)) for seen in seen_patterns):
            filtered_counter[pattern_without_equals] = count
            seen_patterns.add(pattern_without_equals)

    return filtered_counter


def process_patch_pairs(patch_pairs):
    """パッチのペアからパターンカウンターとトリガーシーケンスカウンターを計算する

    Args:
        patch_pairs (list): 変更前後のコードのペアのリスト

    Returns:
        tuple: パターンカウンター、トリガーシーケンスカウンター、実際に変更されたカウンター
    """
    pattern_counter = Counter()
    triggerable_initial = Counter()
    actually_changed = Counter()

    for condition, consequent in patch_pairs:
        diff_tokens = compute_token_diff(condition, consequent)
        if not diff_tokens:
            continue
        merged_diff_tokens = merge_consecutive_tokens(diff_tokens)
        new_patterns = extract_valid_subsequences(merged_diff_tokens)
        update_pattern_counter(pattern_counter, merged_diff_tokens)

        for pattern in new_patterns:
            trigger_sequence = extract_trigger_sequence(pattern)
            triggerable_initial[trigger_sequence] += new_patterns[pattern]
            actually_changed[pattern] += new_patterns[pattern]

    return filter_patterns(pattern_counter, triggerable_initial, actually_changed)
    # return pattern_counter, triggerable_initial, actually_changed


if __name__ == "__main__":
    patch_pairs = [
        ("i = dic[STRING]", "i = dic.get(STRING)"),
        ("i = dic[STRING]", "i = dic.get(STRING)"),
        ("x = y + z", "x = y * z"),
        ("foo = bar()", "foo = baz()"),
    ]
    print(process_patch_pairs(patch_pairs))
