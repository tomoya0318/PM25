import difflib
import tokenize

from pathlib import Path
from typing import Generator

from abstractor.abstraction import abstract_code
from codetokenizer.tokenizer import TokeNizer
from constants import path
from exception import TokenizationError
from gumtree.extractor import extract_update_code_changes
from gumtree.runner import GumTreeResponse, run_GumTree
from models.diff import DiffHunk
from models.gumtree import UpdateChange
from utils.diff_handler import DiffDataHandler
from utils.lang_identifiyer import identify_lang_from_file


def extract_diff(file_path: Path) -> Generator[list[str], None, None]:
    """JSONファイルから，変更前と変更後のペアを抽出する

    Args:
        file_path (str): データを含むJSONファイルへのパス

    Returns:
        list[(language: str, DiffHunk(condition: list, consequent: list))]
    """
    DH = DiffDataHandler

    for item in DH.load_from_json(file_path):
        try:
            language = identify_lang_from_file(item.file_name)
            # Pythonファイルのみに対応
            if language != "Python":
                continue
        except ValueError as e:
            print(e)
            continue
        else:
            condition = item.diff_hunk.condition
            consequent = item.diff_hunk.consequent

            abstracted_diff = abstract_code(DiffHunk(condition, consequent))

            if len(abstracted_diff.condition) > 5 or len(abstracted_diff.consequent) > 5:
                continue

            elif (
                len(abstracted_diff.condition) != len(abstracted_diff.consequent)
                or len(abstracted_diff.condition) == 1
            ):
                token_diff = _compute_token_diff(language, DiffHunk(condition, consequent))
                yield token_diff

            else:
                response: GumTreeResponse = run_GumTree(abstracted_diff.condition, abstracted_diff.consequent)
                changes: list[UpdateChange] = extract_update_code_changes(
                    abstracted_diff.condition, abstracted_diff.consequent, response.actions
                )
                for change in changes:
                    token_diff = _compute_token_diff(language, DiffHunk([change.before], [change.after]))
                    yield token_diff


def _tokenize_diff(language: str, code: list[str]):
    TN = TokeNizer(language)
    tokenized_code = []
    try:
        for line in code:
            tokenized_code.extend(TN.getPureTokens(line))
        return tokenized_code
    except tokenize.TokenError as e:
        raise TokenizationError(f"Failed to tokenize code: {str(e)}") from e


def _compute_token_diff(language: str, diff_hunk: DiffHunk) -> list[str]:
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
    file_path = path.RESOURCE / "numpy" / "numpy.json"
    for diff in extract_diff(file_path):
        print(f"diff: {diff}")
