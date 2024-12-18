from difflib import Differ

from models.diff import DiffHunk
from constants import path
from diff.comment_remover import remove_comments, remove_docstring


def _parse_diff(diff: list) -> list[DiffHunk]:
    diff_data: list[DiffHunk] = []

    def _append_non_empty_line(content: list[str], line: str):
        line = line[1:].strip()
        if line != "":
            content.append(line)

    def _save_current_diff(condition, consequent) -> None:
        if condition and consequent:
            diff_data.append(DiffHunk(condition, consequent))

    try:
        pos = 0
        condition, consequent = [], []

        while pos < len(diff):
            line: str = diff[pos]
            if line.startswith("?"):
                pos += 1
                continue
            elif line.startswith("-"):
                _append_non_empty_line(condition, line)
                pos += 1

            elif line.startswith("+"):
                while pos < len(diff) and diff[pos].startswith("+"):
                    _append_non_empty_line(consequent, diff[pos])
                    pos += 1
                _save_current_diff(condition, consequent)
                condition, consequent = [], []

            else:
                _save_current_diff(condition, consequent)
                condition, consequent = [], []
                pos += 1

        return diff_data

    except Exception as e:
        raise Exception(f"Failed to generate diff: {str(e)}")


def get_diff(base_file: str, target_file: str) -> list[DiffHunk]:
    # コメントの削除
    del_comment_base_file = remove_comments(base_file)
    del_comment_target_file = remove_comments(target_file)

    # docstringの削除
    cleaned_base_file = remove_docstring(del_comment_base_file)
    cleaned_target_file = remove_docstring(del_comment_target_file)

    d = Differ()
    diff = list(d.compare(cleaned_base_file.splitlines(), cleaned_target_file.splitlines()))

    return _parse_diff(diff)
