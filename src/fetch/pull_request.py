from git import DiffIndex, Repo, GitCommandError
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Generator
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
    def __init__(self, token, start_date, end_date):
        self.headers = {"Authorization": f"token {token}"}
        self.base_url = "https://api.github.com"
        self.start_date = start_date
        self.end_date = end_date

    def clone_project(self, owner: str, repo: str) -> Repo:
        dir_path = path.TMP / repo
        url = f"https://github.com/{owner}/{repo}.git"
        print(f"cloning from {url}")
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
            print(f"Rate limit reached. Wait for {wait_time:.2f} seconds.")
            time.sleep(wait_time)  # wait_time秒だけ待機
            return self._make_request(url, params)
        elif response.status_code != 200:
            raise GitHubAPIError(f"API request failed {response.text}")

        return response.json()

    def _yield_pulls_data(
        self,
        owner: str,
        repo: str,
        state: str = "all",
    ) -> Generator[dict, None, None]:
        page = 1
        per_page = 100
        while True:
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
            params = {"state": state, "page": page, "per_page": per_page, "sort": "updated", "direction": "desc"}
            print(f"fetching from {url}, page: {page}")
            prs = self._make_request(url, params)

            if not prs:
                break

            for pr in prs:
                pr_updated_at = datetime.strptime(pr["updated_at"], "%Y-%m-%dT%H:%M:%SZ")

                # 終了日が指定されていて、PRの更新日が終了日より後の場合はスキップ
                if self.end_date and pr_updated_at > self.end_date:
                    continue

                # 開始日が指定されていて、PRの更新日が開始日より前の場合は全ての取得を終了
                if self.start_date and pr_updated_at < self.start_date:
                    return
                yield pr
            page += 1

    def _yield_merged_prs_number(self, owner: str, repo: str) -> Generator[int, None, None]:
        closed_prs = self._yield_pulls_data(owner, repo, "close")
        for pr in closed_prs:
            if pr["merged_at"] is not None:
                yield pr["number"]

    def _fetch_pr_commit_hashes(self, owner: str, repo: str, pr_number: int) -> list[str]:
        """指定したプルリクエストの全てのコミットハッシュを取得する"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        commits = self._make_request(url)
        return [commit["sha"] for commit in commits]

    def _fetch_commit_details(self, owner: str, repo: str, commit_sha: str) -> tuple[list[str], str]:
        """指定したコミットハッシュで変更されたファイルの一覧とコミットメッセージを取得する
        Returns:
            tuple[list[str], str]: 変更ファイルの一覧, コミットメッセージの形式で返す
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{commit_sha}"
        commit_data = self._make_request(url)
        changed_files = [file["filename"] for file in commit_data["files"]]
        commit_messages = commit_data["commit"]["message"]
        return changed_files, commit_messages

    def _parse_diff(self, diff: DiffIndex) -> list[ParsedDiff]:
        diff_data = []

        def _save_current_diff(file_name, condition, consequent) -> None:
            if condition and consequent:
                diff_data.append(ParsedDiff(file_name, condition, consequent))

        for d in diff:
            try:
                lines = d.diff.decode("utf-8").splitlines()
                pos = 0
                condition, consequent = [], []
                file_name = d.a_path

                while pos < len(lines):
                    line = lines[pos]

                    if line.startswith("-"):
                        condition.append(line[1:].strip())
                        pos += 1

                    elif line.startswith("+"):
                        while pos < len(lines) and lines[pos].startswith("+"):
                            consequent.append(lines[pos][1:].strip())
                            pos += 1
                        _save_current_diff(file_name, condition, consequent)
                        condition, consequent = [], []

                    else:
                        _save_current_diff(file_name, condition, consequent)
                        condition, consequent = [], []
                        pos += 1

            except Exception as e:
                print(f"Failed to generate diff: {str(e)}")
                continue

        return diff_data

    def _get_commit_diff(
        self, repo: Repo, base_commit_hash: str, target_commit_hash: str, file_name: str
    ) -> list[ParsedDiff]:
        base_commit = repo.commit(base_commit_hash)
        target_commit = repo.commit(target_commit_hash)

        if not base_commit or not target_commit:
            raise GitCommandError(f"Could not access required commits")

        diffs: DiffIndex = base_commit.diff(target_commit, create_patch=True, paths=file_name)
        return self._parse_diff(diffs)

    def _fetch_pr_details(self, owner: str, repo: str, pr_number: int) -> dict:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        return self._make_request(url)

    def get_all_pr_commit_diff(self, owner: str, repo: str) -> list[DiffData]:
        """全てのマージ済みPRのコミットハッシュを取得"""
        repo_data: Repo = self.clone_project(owner, repo)
        diff_data = []

        for pr_number in self._yield_merged_prs_number(owner, repo):
            try:
                print(f"fetching PR #{pr_number} details...")
                pr_details = self._fetch_pr_details(owner, repo, pr_number)

                print(f"fetching commit hashes from PR #{pr_number}")
                commit_hashes = self._fetch_pr_commit_hashes(owner, repo, pr_number)
                # PRの最初と最後のコミットの差分取得（レビュワーの意思反映のため）
                if len(commit_hashes) <= 1:
                    continue

                # PR内で変更があったファイルを取得
                print(f"fetching changed file ...")
                commit_messages = {}
                file_change = {}

                for commit_sha in commit_hashes:
                    changed_files, commit_message = analyzer._fetch_commit_details(owner, repo, commit_sha)
                    commit_messages[commit_sha] = commit_message

                    for changed_file in changed_files:
                        if changed_file in file_change:
                            file_change[changed_file].append(commit_sha)
                        else:
                            file_change[changed_file] = [commit_sha]

                # 各ファイルに2つのコミットがないものを除外
                file_change = {file: hashes for file, hashes in file_change.items() if len(hashes) >= 2}

                # ファイルごとにdiffを取得
                print(f"getting diffs...")
                for file_name, hashes in file_change.items():
                    diffs = self._get_commit_diff(repo_data, hashes[0], hashes[-1], file_name)
                    merged_date = datetime.strptime(pr_details["merged_at"], "%Y-%m-%dT%H:%M:%SZ")
                    for diff in diffs:
                        diff_data.append(
                            DiffData(
                                file_name=diff.file_name,
                                pr_number=pr_number,
                                base_hash=hashes[0],
                                target_hash=hashes[-1],
                                diff_hunk=DiffHunk(diff.condition, diff.consequent),
                                merged_date=merged_date,
                                base_message=commit_messages[hashes[0]],
                                target_message=commit_messages[hashes[-1]],
                            )
                        )

                # 成功したPRデータを保存する
                output_path = path.RESOURCE / owner / f"{repo}.json"
                Dh.dump_to_json(diff_data, output_path, owner, repo)

            except GitHubAPIError as e:
                print(f"Error fetching commits for PR #{pr_number}: {str(e)}")
                # エラーが発生した場合でも、それまでのデータは保存する
                output_path = path.RESOURCE / owner / f"{repo}.json"
                Dh.dump_to_json(diff_data, output_path, owner, repo)
                continue

            time.sleep(0.5)

        return diff_data


if __name__ == "__main__":
    owner = "numpy"
    repo = "numpy"
    output_path = path.RESOURCE / owner / f"{repo}.json"
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    # 期間を指定
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2024, 1, 1)
    analyzer = GitHubPRAnalyzer(token, start_date, end_date)
    Dh = DiffDataHandler

    repo1 = Repo(path.TMP / repo)
    analyzer.get_all_pr_commit_diff(owner, repo)
