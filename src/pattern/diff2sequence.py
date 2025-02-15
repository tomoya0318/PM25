import os
import tokenize
from datetime import datetime
from pathlib import Path
from typing import Generator


import difflib
from codetokenizer.tokenizer import TokeNizer

from abstractor.abstraction import abstract_code
from exception import TokenizationError
from gumtree.extractor import extract_update_code_changes
from models.diff import DiffHunk
from models.gumtree import UpdateChange
from utils.diff_handler import DiffDataHandler
from utils.lang_identifiyer import identify_lang_from_file

if os.path.isfile("/.dockerenv"):
    from gumtree.runner_in_docker import run_GumTree
else:
    from gumtree.runner import run_GumTree


def extract_diff(file_path: Path) -> Generator[tuple[datetime, str, DiffHunk], None, None]:
    """JSONファイルから，変更前と変更後のペアを抽出する"""

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
                token_diff = DiffHunk(abstracted_diff.condition, abstracted_diff.consequent)
                yield item.merged_at, language, token_diff

            else:
                response = run_GumTree(abstracted_diff.condition, abstracted_diff.consequent)
                changes: list[UpdateChange] = extract_update_code_changes(
                    abstracted_diff.condition, abstracted_diff.consequent, response.actions
                )
                for change in changes:
                    token_diff = DiffHunk([change.before], [change.after])
                    yield item.merged_at, language, token_diff


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


def merge_consecutive_tokens(diff: list[str]) -> list[str]:
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
    condition = ['a = a + b']
    consequent = ['a += b']
    print(compute_token_diff("Python", DiffHunk(condition, consequent)))