import os
from git import Repo
from constants import path
from utils.file_processor import ensure_dir_exists, dump_to_json, get_filename
from models.diff import DiffHunk


def clone_project(url: str) -> Repo | str:
    dir_path = f"{path.TMP}/{get_filename(url)}"
    ensure_dir_exists(dir_path)
    try:
        if os.path.exists(dir_path):
            repo = Repo(dir_path)
            print("project already exists, updating...")
        else:
            print(f"Cloning from {url}...")
            # 完全な履歴でクローン
            repo = Repo.clone_from(url, dir_path, no_single_branch=True)
            print("Clone completed")
        return repo
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


def get_hash_diff(repo: Repo, commit_hash: str) -> str:
    try:
        # まず、指定されたコミットハッシュの取得を試みる
        try:
            repo.remote().fetch(f"+refs/heads/*:refs/remotes/origin/*")
            repo.git.fetch("origin", commit_hash)
            print(f"Successfully fetched commit {commit_hash}")
        except Exception as e:
            print(f"Fetch commit failed: {str(e)}")

        commit = repo.commit(commit_hash)
        if not commit.parents:
            return f"エラーが発生しました: Commit {commit_hash} has no parent commit"

        parent = commit.parents[0]
        try:
            diff = parent.diff(commit, create_patch=True)

            diff_output = ""
            for d in diff:
                diff_output += f"File: {d.a_path}\n"
                diff_output += d.diff.decode("utf-8")
                diff_output += "\n\n"
            return diff_output

        except Exception as e:
            return f"エラーが発生しました: Failed to generate diff - {str(e)}"

    except Exception as e:
        return f"エラーが発生しました: Failed to find commit {commit_hash} - {str(e)}"


def parse_diff(diff: str) -> list[dict[str, str | list]]:
    result: list[dict[str, str | list]] = []
    current_file: str | None = None
    current_hunk: DiffHunk | None = None
    lines = diff.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("File:"):
            current_file = line.split("File:", 1)[-1]
            current_hunk = DiffHunk([], [])
            i += 1
            continue
        if current_file is not None and current_hunk is not None and line.startswith("-"):
            current_hunk.condition.append(line[1:].strip())
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith("-"):
                    current_hunk.condition.append(next_line[1:].strip())
                    i += 1
                    continue
                if next_line.startswith("+"):
                    current_hunk.consequent.append(next_line[1:].strip())
                    i += 1
                    continue
                result.append(
                    {"File": current_file, "condition": current_hunk.condition, "consequnet": current_hunk.consequent}
                )
                current_hunk = DiffHunk([], [])
                break
            continue
        i += 1

    return result


def save_diff_to_file(diff_content, output_file):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(diff_content)
        print(f"Diff content saved to {output_file}")
    except Exception as e:
        print(f"ファイルの保存中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    repo_url = "https://github.com/facebook/react-native.git"
    commit_hash = "e9150befa953dce17e2b9ca273082c2f502a3e0c"
    output_file = f"{path.INTERMEDIATE}/sample/react-native#27850.json"

    repo = clone_project(repo_url)
    if isinstance(repo, Repo):
        print("Repository operations completed")
        diff = get_hash_diff(repo, commit_hash)
        if not diff.startswith("エラーが発生しました"):
            hunk_diff = parse_diff(diff)
            dump_to_json(hunk_diff, output_file)
            print(f"Successfully separate diff to {output_file}")
        else:
            print(diff)
    else:
        print(repo)
