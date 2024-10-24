import os
from git import Repo
from constants import path
from utils.file_processor import ensure_dir_exists, dump_to_json, get_filename


def clone_project(url: str) -> Repo | str:
    dir_path = f"{path.TMP}/{get_filename(url)}"
    ensure_dir_exists(dir_path)
    try:
        if os.path.exists(dir_path):
            repo = Repo(dir_path)
            print(f"project already exist")
        else:
            repo = Repo.clone_from(url, dir_path)
            print(f"cloned from {url}")
        return repo
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


def get_hash_diff(repo: Repo, commit_hash: str) -> str:
    try:
        commit = repo.commit(commit_hash)
        parent = commit.parents[0]
        diff = parent.diff(commit, create_patch=True)

        diff_output = ""
        for d in diff:
            diff_output += f"File: {d.a_path}\n"
            diff_output += d.diff.decode("utf-8")
            diff_output += "\n\n"
        return diff_output
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


def parse_diff(diff: str):
    result: list[dict[str, str | list]] = []
    file_name: str = ""
    lines = diff.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("File:"):
            file_name = line.split("File:", 1)[-1]
        if line.startswith("-"):
            for plus_line in lines[i + 1 :]:
                if plus_line.startswith("+"):
                    result.append({"File": file_name, "condition": [line[1:]], "consequent": [plus_line[1:]]})
                break

    return result


def save_diff_to_file(diff_content, output_file):
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(diff_content)
        print(f"Diff content saved to {output_file}")
    except Exception as e:
        print(f"ファイルの保存中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    repo_url = "https://github.com/microsoft/vscode.git"
    commit_hash = "3f6ca9427914002d51c4ca6ad48f29e47cc60529"
    output_file = f"{path.RESULTS}/diff.json"
    repo = clone_project(repo_url)
    if isinstance(repo, Repo):
        diff = get_hash_diff(repo, commit_hash)
        if not diff.startswith("エラーが発生しました"):
            result = parse_diff(diff)
            dump_to_json(result, output_file)
        else:
            print(diff)
    else:
        print(repo)
