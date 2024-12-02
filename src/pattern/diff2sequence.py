import difflib
import tokenize

from codetokenizer.tokenizer import TokeNizer
from constants import path
from exception import TokenizationError
from abstractor.abstraction import abstract_code
from gumtree.extractor import extract_update_code_changes
from gumtree.runner import GumTreeResponse, run_GumTree
from models.diff import DiffHunk
from models.gumtree import UpdateChange
from utils.file_processor import load_from_json
from utils.lang_identifiyer import identify_lang_from_file


def extract_diff(file_path: str) -> list[tuple[str, DiffHunk]]:
    """JSONファイルから，変更前と変更後のペアを抽出する

    Args:
        file_path (str): データを含むJSONファイルへのパス

    Returns:
        list[(language: str, DiffHunk(condition: list, consequent: list))]
    """
    data = load_from_json(file_path)
    result = []

    for item in data:
        try:
            language = identify_lang_from_file(item["File"])
        except ValueError as e:
            print(e)
            continue
        else:
            condition = item["condition"]
            consequent = item["consequent"]

            abstracted_diff = abstract_code(DiffHunk(condition, consequent))
            if (
                len(abstracted_diff.condition) != len(abstracted_diff.consequent)
                or len(abstracted_diff.condition) == 1
            ):
                result.append([language, DiffHunk(abstracted_diff.condition, abstracted_diff.consequent)])
                continue

            else:
                response: GumTreeResponse = run_GumTree(abstracted_diff.condition, abstracted_diff.consequent)
                changes: list[UpdateChange] = extract_update_code_changes(
                    abstracted_diff.condition, abstracted_diff.consequent, response.actions
                )
                for change in changes:
                    result.append([language, DiffHunk(condition=[change.before], consequent=[change.after])])
                continue

    return result


def _tokenize_diff(language: str, code: list[str]):
    TN = TokeNizer(language)
    tokenized_code = []
    try:
        for line in code:
            tokenized_code.extend(TN.getPureTokens(line))
        return tokenized_code
    except tokenize.TokenError as e:
        raise TokenizationError(f"Failed to tokenize code: {str(e)}") from e


def compute_token_diff(language: str, diff_hunk: DiffHunk) -> list[str]:
    """トークン化された2つのコード文字列の差分を計算する．"""
    tokenized_condition = _tokenize_diff(language, diff_hunk.condition)
    tokenized_consequent = _tokenize_diff(language, diff_hunk.consequent)

    diff = []

    sm = difflib.SequenceMatcher(None, tokenized_condition, tokenized_consequent)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            for token in tokenized_condition[i1:i2]:
                diff.append(f"-{token}")
            for token in tokenized_consequent[j1:j2]:
                diff.append(f"+{token}")
        elif tag == "delete":
            for token in tokenized_condition[i1:i2]:
                diff.append(f"-{token}")
        elif tag == "insert":
            for token in tokenized_consequent[j1:j2]:
                diff.append(f"+{token}")
        elif tag == "equal":
            for token in tokenized_condition[i1:i2]:
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

    for token in diff[1:]:
        if current_token.startswith(("-", "+", "=")) and token.startswith(current_token[0]):
            current_token += token[1:]
            continue
        merged_diff.append(current_token)
        current_token = token

    merged_diff.append(current_token)
    return merged_diff


if __name__ == "__main__":
    file_path = f"{path.INTERMEDIATE}/sample/vscode#88117.json"
    diffs = extract_diff(file_path)

    print(diffs)
    for lang, diff_hunk in diffs:
        token_diff = compute_token_diff(lang, diff_hunk)
        print(token_diff)
