import os
import re
import tokenize
from enum import Enum

from codetokenizer.tokenizer import TokeNizer

from abstractor.loder import IdentifierDict
from exception import TokenizationError
from models.diff import DiffHunk
from models.gumtree import GumTreeResponse

if os.path.isfile("/.dockerenv"):
    from gumtree.runner_in_docker import run_GumTree
else:
    from gumtree.runner import run_GumTree


class Abstraction(Enum):
    VAR = 1
    STRING = 2
    NUMBER = 3


def tokenize_code(code_line: str) -> list[str]:
    LANGUAGE = "Python"
    TN = TokeNizer(LANGUAGE)
    try:
        return TN.getPureTokens(code_line)
    except tokenize.TokenError as e:
        raise TokenizationError(f"Failed to tokenize code: {str(e)}") from e


def replace_name(line: str, old_name: str, new_name: str) -> str:
    """行内の関数名を置換"""
    # 関数定義のパターン
    pattern = re.escape(old_name)
    return re.sub(pattern, f"{new_name}", line)


def abstract_function_names(diff_hunk: DiffHunk) -> DiffHunk:
    name_mapping = {}

    def abstract_names(src_code: list[str]) -> list[str]:
        abstracted_code = []
        for line in src_code:
            try:
                tokens = tokenize_code(line)
                if "def" not in tokens:
                    abstracted_code.append(line)
                    continue

                func_index = tokens.index("def") + 1
                if func_index >= len(tokens):
                    continue

                func_name = tokens[func_index]
                if func_name not in name_mapping:
                    name_mapping[func_name] = f"FUNCTION_{len(name_mapping) + 1}"

                abstracted_code.append(replace_name(line, func_name, name_mapping[func_name]))
            except TokenizationError as e:
                print(e)
                continue

        return abstracted_code

    return DiffHunk(abstract_names(diff_hunk.condition), abstract_names(diff_hunk.consequent))


def abstract_code(diff_hunk: DiffHunk) -> DiffHunk:
    name_mapping = {}
    ID = IdentifierDict()
    var_count = str_count = num_count = 1

    # 関数名だけ先に抽象化
    diff_hunk = abstract_function_names(diff_hunk)

    # gumtreeで抽象構文木で分析
    response: GumTreeResponse = run_GumTree(diff_hunk.condition, diff_hunk.consequent)

    # 抽象化を行う関数
    def _abstract_name(src_code: list[str], target_token: str, match: Abstraction):
        nonlocal name_mapping, var_count, str_count, num_count
        abstracted_code = []
        for line in src_code:
            if target_token not in line:
                abstracted_code.append(line)
                continue
            if target_token not in name_mapping:
                if match == Abstraction.VAR:
                    name_mapping[target_token] = f"VAR_{var_count}"
                    var_count += 1
                elif match == Abstraction.STRING:
                    name_mapping[target_token] = f"STRING_{str_count}"
                    str_count += 1
                elif match == Abstraction.NUMBER:
                    name_mapping[target_token] = f"NUBER_{num_count}"
                    num_count += 1

            abstracted_code.append(replace_name(line, target_token, name_mapping[target_token]))
        return abstracted_code

    # 文字列のトークン特定用
    def _extract_string_literal(src_code: list, start: int, end: int) -> str:
        joined_code = "\n".join(src_code)
        return joined_code[start:end]

    for match in response.matches:
        if "identifier:" in match.src:
            # matchしたトークンの特定
            try:
                src_token = match.src.split(":")[1].split("[")[0].strip()
                dest_token = match.dest.split(":")[1].split("[")[0].strip()

                # 一般的なメソッド名などではないか判定
                if ID.should_preserve(src_token):
                    continue

                if "FUNCTION" in src_token or "FUCTION" in dest_token:
                    continue

                diff_hunk = DiffHunk(
                    _abstract_name(diff_hunk.condition, src_token, Abstraction.VAR),
                    _abstract_name(diff_hunk.consequent, dest_token, Abstraction.VAR),
                )
            except IndexError:
                print(match)
                continue

        if "integer:" in match.src:
            try:
                src_token = match.src.split(":")[1].split("[")[0].strip()
                dest_token = match.dest.split(":")[1].split("[")[0].strip()

                diff_hunk = DiffHunk(
                    _abstract_name(diff_hunk.condition, src_token, Abstraction.NUMBER),
                    _abstract_name(diff_hunk.consequent, dest_token, Abstraction.NUMBER),
                )
            except IndexError:
                print(match)
                continue

        if match.src.startswith("string ["):
            try:
                # 変更前の文字列の位置情報を取得
                src_pos = match.src.split("[")[1].split("]")[0]
                src_start, src_end = map(int, src_pos.split(","))

                # 変更後の文字列の位置情報を取得
                dest_pos = match.dest.split("[")[1].split("]")[0]
                dest_start, dest_end = map(int, dest_pos.split(","))

                src_token = _extract_string_literal(diff_hunk.condition, src_start, src_end)
                dest_token = _extract_string_literal(diff_hunk.consequent, dest_start, dest_end)

                diff_hunk = DiffHunk(
                    _abstract_name(diff_hunk.condition, src_token, Abstraction.STRING),
                    _abstract_name(diff_hunk.consequent, dest_token, Abstraction.STRING),
                )
            except IndexError:
                print(match)
                continue

    return diff_hunk


if __name__ == "__main__":
    condition = ["def func(a)"]
    consequent = ["def func(a + b)"]

    print(abstract_code(DiffHunk(condition, consequent)))
