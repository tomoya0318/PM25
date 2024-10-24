import difflib
from collections import Counter
from itertools import combinations
import tokenize
from tqdm import tqdm
from codetokenizer.tokenizer import TokeNizer
from pattern.code2diff.source_preprocessor import variable_name_preprocessing, extract_diff
from utils.file_processor import dump_to_json, load_from_json, list_files_in_directory
from constants import path


def compute_token_diff(condition: str, consequent: str, language: str) -> list[str] | dict[str, str]:
    """トークン化された2つのコード文字列の差分を計算する．

    Args:
        condition (str): 変更前のコード文字列
        consequent (str): 変更後のコード文字列

    Returns:
        list: 差分を示すトークンのリスト．削除されたトークンには「-」、追加されたトークンには「+」が付く．
    """
    TN = TokeNizer(language)
    try:
        token_condition = TN.getPureTokens(variable_name_preprocessing(condition))
        token_consequent = TN.getPureTokens(variable_name_preprocessing(consequent))
    except tokenize.TokenError as e:
        return {"error": str(e)}

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

    for token in tqdm(diff[1:], desc="merging token", leave=False):
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

    def subsequence_generator(tokens):
        start_token = tokens[0]
        n = len(tokens)
        for length in range(2, n + 1):  # 部分列の長さを2からnまで変更
            for comb in combinations(range(1, n), length - 1):  # 各長さで部分列を生成（start_tokenを固定）
                subseq = (start_token,) + tuple(tokens[i] for i in comb)
                if any(token.startswith(("-", "+")) for token in subseq):
                    yield subseq

    subseq_counter = Counter()
    for subseq in tqdm(subsequence_generator(tokens), desc="extract_subsequences", leave=False):
        subseq_counter[subseq] += 1

    return subseq_counter


def extract_trigger_sequence(pattern):
    """パターンからトリガーシーケンスを抽出する．

    Args:
        pattern (tuple): パターンのトークンシーケンス

    Returns:
        str: トリガーシーケンスのトークンシーケンスを文字列で返す
    """
    trigger_sequence = " ".join(
        token.lstrip("-=") for token in pattern if token.startswith("=") or token.startswith("-")
    )
    return trigger_sequence


def extract_pattern_change(pattern):
    """パターンから変更部後のシーケンスを抽出する．

    Args:
        pattern (tuple): パターンのトークンシーケンス

    Returns:
        str: 変更部分のトークンシーケンスを文字列で返す
    """
    pattern_changed = " ".join(
        token.lstrip("+=") for token in pattern if token.startswith("=") or token.startswith("+")
    )
    return pattern_changed


def update_pattern_counter(counter, new_tokens):
    """既存のパターンカウンターに新しいトークンリストから抽出したパターンの頻度を追加する

    Args:
        counter (Counter): 既存のパターンカウンター
        new_tokens (list): 新しいトークンのリスト
    """
    new_subsequences = extract_valid_subsequences(new_tokens)
    counter.update(new_subsequences)


def _contains_plus_and_minus(pattern):
    """パターンに`-`と`+`が同時に存在するかを確認する

    パターン内に変更を示す`-`（削除）と`+`（追加）が
    両方存在するかどうかをチェックする。

    Args:
        pattern (list): パターンのリスト

    Returns:
        bool: `-`と`+`が両方存在する場合はTrue、そうでない場合はFalse
    """
    contains_minus = any(token.startswith("-") for token in pattern)
    contains_plus = any(token.startswith("+") for token in pattern)
    return contains_minus and contains_plus


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
    for pattern, count in tqdm(sorted(counter.items(), key=lambda x: -len(x[0])), desc="fillting...", leave=False):
        # 1度しか出現していないパターンを削除
        if count <= 1:
            continue

        # 変更を提案しないコード（`-`と`+`が同時に存在しないパターン）を削除
        if not _contains_plus_and_minus(pattern):
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

        # 同じトークンが含まれる大きいパターンを優先
        if not any(set(pattern).issubset(set(seen)) for seen in seen_patterns):
            filtered_counter[pattern] = count
            seen_patterns.add(pattern)

    return filtered_counter


def process_patch_pairs(patch_pairs, language):
    """パッチのペアからパターンカウンターとトリガーシーケンスカウンターを計算する

    Args:
        patch_pairs (list): 変更前後のコードのペアのリスト

    Returns:
        tuple: パターンカウンター、トリガーシーケンスカウンター、実際に変更されたカウンター
    """
    pattern_counter = Counter()
    triggerable_initial = Counter()
    actually_changed = Counter()

    for condition, consequent in tqdm(patch_pairs, desc="process patch", leave=False):
        diff_tokens = compute_token_diff(condition, consequent, language)
        if not diff_tokens:
            continue
        merged_diff_tokens = merge_consecutive_tokens(diff_tokens)
        new_patterns = extract_valid_subsequences(merged_diff_tokens)
        update_pattern_counter(pattern_counter, merged_diff_tokens)

        for pattern in tqdm(new_patterns, desc="getting trigger and actually", leave=False):
            trigger_sequence = extract_trigger_sequence(pattern)
            triggerable_initial[trigger_sequence] += new_patterns[pattern]
            actually_changed[pattern] += new_patterns[pattern]

    return filter_patterns(pattern_counter, triggerable_initial, actually_changed)


def save_to_tempfile(data):
    tmp_file_path = f"{path.TMP}/tmp_patch_pairs.json"
    dump_to_json(data, tmp_file_path)
    return tmp_file_path


def load_from_tmpfile(file_path, batch_size):
    data = load_from_json(file_path)
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


def main():
    project = f"{path.INTERMEDIATE}/sample/vscode#87709.json"
    out_path = f"{path.RESULTS}/sample/vscode#87709.json"
    patch_data = extract_diff(project)
    result = []
    for language, condition, consequent in patch_data:
        diff = compute_token_diff(condition, consequent, language)
        if isinstance(diff, dict) and "error" in diff:
            print(f"エラーが発生しました: {diff["error"]}")
            continue
        if isinstance(diff, list) and not diff:
            continue
        merged_diff = merge_consecutive_tokens(diff)
        result.append(merged_diff)
    dump_to_json(result, out_path)


if __name__ == "__main__":
    main()
