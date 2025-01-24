from git import Repo, GitCommandError
from pathlib import Path

from constants import path


def clone_project(url: str, repo: str, branch: str = "master"):
    dir_path = path.TMP / repo
    print(f"cloning from {url}")

    try:
        if not dir_path.exists():
            repo_data = Repo.clone_from(url, dir_path, branch=branch, shallow_since="2015-12-01")
        else:
            repo_data = Repo(dir_path)
        return repo_data
    except GitCommandError as e:
        raise GitCommandError(f"Git Command failed: {str(e)}")


def checkout_commit(repo: Repo, commit_hash: str):
    try:
        repo.git.checkout(commit_hash)
    except GitCommandError as e:
        raise GitCommandError(f"Git Command failed: {str(e)}")
