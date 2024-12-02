import re

from gumtree.runner import run_GumTree
from models.gumtree import GumTreeResponse
from models.diff import DiffHunk


def _extract_string_literal(code: list, start: int, end: int) -> str:
        joined_code = "".join(code)
        return joined_code[start:end]


def abstract_code(diff_hunk: DiffHunk) -> DiffHunk:
    response: GumTreeResponse = run_GumTree(diff_hunk.condition, diff_hunk.consequent)
    # print(response)
    abstraction_map = {}
    string_map = {}

    for match in response.matches:
        if "identifier:" in match.src:
            #識別子が変更前後で同じものだけ抽象化
            src_id = match.src.split(":")[1].split("[")[0].strip()
            dest_id = match.dest.split(":")[1].split("[")[0].strip()

            if src_id == dest_id:
                abstraction_map[src_id] = "IDENTIFIER"
                continue

        if "integer:" in match.src:
            src_int = match.src.split(":")[1].split("[")[0].strip()
            dest_int = match.dest.split(":")[1].split("[")[0].strip()

            if src_int == dest_int:
                abstraction_map[src_int] = "NUMBER"

        if match.src.startswith('string ['):
            # 変更前の文字列の位置情報を取得
            src_pos = match.src.split('[')[1].split(']')[0]
            src_start, src_end = map(int, src_pos.split(','))

            # 変更後の文字列の位置情報を取得
            dest_pos = match.dest.split('[')[1].split(']')[0]
            dest_start, dest_end = map(int, dest_pos.split(','))

            src_string = _extract_string_literal(diff_hunk.condition, src_start, src_end)
            dest_string = _extract_string_literal(diff_hunk.consequent, dest_start, dest_end)

            if src_string == dest_string:
                string_map[src_string] = "STRING"
                continue

    def abstract_line(line: str) -> str:
        result = line

        #識別子と数値の抽象化
        for id_name, replacement in abstraction_map.items():
            pattern = r'\b' + re.escape(id_name) + r'\b'
            result = re.sub(pattern, replacement, result)

        #文字列の抽象化
        for string_literal, replacement in string_map.items():
            pattern = re.escape(string_literal)
            result = re.sub(pattern, replacement, result)

        return result

    abstracted_condition = [abstract_line(line) for line in diff_hunk.condition]
    abstracted_consequent = [abstract_line(line) for line in diff_hunk.consequent]

    return DiffHunk(abstracted_condition, abstracted_consequent)

if __name__ == "__main__":
    condition = [
        "a = 2"
    ]
    consequent = [
        "b = 2"
    ]
    print(abstract_code(DiffHunk(condition, consequent)))