from difflib import Differ

from dataclasses import dataclass
from git import Repo, GitCommandError

from diff.comment_remover import remove_comments, remove_docstring


@dataclass
class ParsedDiff:
    file_name: str
    condition: list[str]
    consequent: list[str]


def _parse_diff(file_name: str, diff: list) -> list[ParsedDiff]:
    diff_data: list[ParsedDiff] = []

    def _append_non_empty_line(content: list[str], line: str):
        line = line[1:].strip()
        if line != "":
            content.append(line)

    def _save_current_diff(file_name, condition, consequent) -> None:
        if condition and consequent:
            diff_data.append(ParsedDiff(file_name, condition, consequent))

    try:
        pos = 0
        condition, consequent = [], []

        while pos < len(diff):
            line = diff[pos]

            if line.startswith("-"):
                _append_non_empty_line(condition, line)
                pos += 1

            elif line.startswith("+"):
                while pos < len(diff) and diff[pos].startswith("+"):
                    _append_non_empty_line(consequent, diff[pos])
                    pos += 1
                _save_current_diff(file_name, condition, consequent)
                condition, consequent = [], []

            else:
                _save_current_diff(file_name, condition, consequent)
                condition, consequent = [], []
                pos += 1

        return diff_data

    except Exception as e:
        raise Exception(f"Failed to generate diff: {str(e)}")


def _extract_file_from_commit(repo: Repo, commit_hash: str, target_file: str) -> str | None:
    commit = repo.commit(commit_hash)
    if not commit:
        raise GitCommandError(f"Could not access required commits")
    try:
        blob = commit.tree / target_file
    except KeyError as e:
        print(KeyError(e))
        return None
    return blob.data_stream.read().decode("utf-8")


def get_commit_diff(
    repo: Repo, base_commit_hash: str, target_commit_hash: str, file_name: str
) -> list[ParsedDiff] | None:

    # Pythonファイルのみでdiffとる
    base_file = _extract_file_from_commit(repo, base_commit_hash, file_name)
    target_file = _extract_file_from_commit(repo, target_commit_hash, file_name)

    if base_file == None or target_file == None:
        return None

    # コメントの削除
    del_comment_base_file = remove_comments(base_file)
    del_comment_target_file = remove_comments(target_file)

    # docstringの削除
    cleaned_base_file = remove_docstring(del_comment_base_file)
    cleaned_target_file = remove_docstring(del_comment_target_file)

    d = Differ()
    diff = list(d.compare(cleaned_base_file.splitlines(), cleaned_target_file.splitlines()))
    return _parse_diff(file_name, diff)
