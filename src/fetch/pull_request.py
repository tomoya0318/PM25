from git import DiffIndex, Repo, GitCommandError
import json
import os
import time

from dotenv import load_dotenv
from dataclasses import asdict, dataclass
from typing import Generator
from pathlib import Path
import requests

from constants import path
from exception import GitHubAPIError
from models.diff import DiffData, DiffHunk
from utils.diff_handler import DiffDataHandler


@dataclass
class ParsedDiff:
    file_name: str
    condition: list[str]
    consequent: list[str]


class GitHubPRAnalyzer:
    def __init__(self, token):
        self.headers = {"Authorization": f"token {token}"}
        self.base_url = "https://api.github.com"

    def clone_project(self, owner: str, repo: str) -> Repo:
        dir_path = path.TMP / repo
        url = f"https://github.com/{owner}/{repo}.git"
        try:
            if dir_path.exists():
                repo_data = Repo(dir_path)
                repo_data.remotes.origin.fetch("+refs/heads/*:refs/remotes/origin/*")
                repo_data.remotes.origin.fetch("+refs/pull/*:refs/remotes/origin/pr/*")
                return repo_data
            else:
                return Repo.clone_from(
                    url, dir_path, multi_options=["--no-single-branch", "--depth=1000"]  # デフォルトの深さを増やす
                )
        except GitCommandError as e:
            raise GitCommandError(f"Git Command failed: {str(e)}")
        except Exception as e:
            raise e

    def _make_request(self, url: str, params: dict | None = None) -> dict:
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
            wait_time = max(0, reset_time - time.time())
            raise GitHubAPIError(f"Rate limit reached. Wait for {wait_time:.2f} seconds.")
        elif response.status_code != 200:
            raise GitHubAPIError(f"API request failed {response.text}")

        return response.json()

    def _yield_pulls_data(self, owner: str, repo: str, state: str = "all") -> Generator[dict, None, None]:
        page = 1
        per_page = 100
        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {"state": state, "page": page, "per_page": per_page}
            print(f"fetching from {url}, page: {page}")
            prs = self._make_request(url, params)

            if not prs:
                break

            for pr in prs:
                yield pr
            break
            page += 1

    def _yield_merged_prs_number(self, owner: str, repo: str) -> Generator[int, None, None]:
        closed_prs = self._yield_pulls_data(owner, repo, "close")
        for pr in closed_prs:
            if pr["merged_at"] is not None:
                yield pr["number"]

    def get_pr_commit_hashes(self, owner: str, repo: str, pr_number: int) -> list:
        """指定したプルリクエストの全てのコミットハッシュを取得する"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        commits = self._make_request(url)
        return [commit["sha"] for commit in commits]

    def _parse_diff(self, diff: DiffIndex) -> list[ParsedDiff]:
        diff_data = []
        for d in diff:
            try:
                condition, consequent = [], []
                for line in d.diff.decode("utf-8").splitlines():
                    if line.startswith("-"):
                        condition.append(line[1:].strip())
                    elif line.startswith("+"):
                        consequent.append(line[1:].strip())
                diff_data.append(ParsedDiff(d.a_path, condition, consequent))
            except Exception as e:
                print(f"Failed to generate diff: {str(e)}")
                continue

        return diff_data

    def _get_commit_diff(self, repo: Repo, base_commit_hash: str, target_commit_hash: str) -> list[ParsedDiff]:
        base_commit = repo.commit(base_commit_hash)
        target_commit = repo.commit(target_commit_hash)

        if not base_commit or not target_commit:
            raise GitCommandError(f"Could not access required commits")

        diff: DiffIndex = base_commit.diff(target_commit, create_patch=True)
        return self._parse_diff(diff)

    def get_all_pr_commit_diff(self, owner: str, repo: str) -> list[DiffData]:
        """全てのマージ済みPRのコミットハッシュを取得"""
        repo_data: Repo = self.clone_project(owner, repo)
        diff_data = []

        for pr_number in self._yield_merged_prs_number(owner, repo):
            try:
                commits = self.get_pr_commit_hashes(owner, repo, pr_number)
                # PRの最初と最後のコミットの差分取得（レビュワーの意思反映のため）
                if len(commits) == 1:
                    continue
                diffs = self._get_commit_diff(repo_data, commits[0], commits[-1])
                for diff in diffs:
                    diff_data.append(
                        DiffData(
                            file_name=diff.file_name,
                            pr_number=pr_number,
                            base_hash=commits[0],
                            target_hash=commits[-1],
                            diff_hunk=DiffHunk(diff.condition, diff.consequent),
                        )
                    )

            except GitHubAPIError as e:
                print(f"Error fetching commits for PR #{pr_number}: {str(e)}")
                continue

            time.sleep(0.1)

        return diff_data


if __name__ == "__main__":
    owner = "numpy"
    repo = "numpy"
    output_path = path.INTERMEDIATE / "sample" / f"{repo}.json"
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    analyzer = GitHubPRAnalyzer(token)
    Dh = DiffDataHandler

    # 全てのマージ済みPRのコミットハッシュを取得
    pr_commits = analyzer.get_all_pr_commit_diff(owner, repo)
    Dh.dump_to_json(pr_commits, output_path, owner, repo)
