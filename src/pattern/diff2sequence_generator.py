import difflib
import tokenize

from tqdm import tqdm

from codetokenizer.tokenizer import TokeNizer
from constants import path
from exception import TokenizationError
from models.diff import DiffHunk
from utils.file_processor import load_from_json
from utils.lang_identifiyer import identify_lang_from_file


def extract_diff(file_path: str):
    """JSONファイルから，変更前と変更後のペアを抽出する

    Args:
        file_path (str): データを含むJSONファイルへのパス

    Returns:
        list[(language: str, condition: str, consequent: str)]
    """
    data = load_from_json(file_path)
    result = []

    for item in tqdm(data, leave=False):
        try:
            language = identify_lang_from_file(item["File"])
        except ValueError as e:
            print(e)
            continue
        else:
            # ここにGumTreeの処理挟む
            condition = item["condition"]
            consequent = item["consequent"]

            result.append([language, DiffHunk(condition[0], consequent[0])])

    return result


def compute_token_diff(language: str, diff_hunk: DiffHunk) -> list[str]:
    """トークン化された2つのコード文字列の差分を計算する．

    Args:
        condition (str): 変更前のコード文字列
        consequent (str): 変更後のコード文字列

    Returns:
        list: 差分を示すトークンのリスト．削除されたトークンには「-」、追加されたトークンには「+」が付く．
    """
    TN = TokeNizer(language)
    try:
        token_condition = TN.getPureTokens(diff_hunk.condition)
        token_consequent = TN.getPureTokens(diff_hunk.consequent)
    except tokenize.TokenError as e:
        raise TokenizationError(f"Failed to tokenize code: {str(e)}") from e

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


def merge_consecutive_tokens(diff: list) -> list:
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
