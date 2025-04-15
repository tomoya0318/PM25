import json
import os
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Generator
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from sqlmodel import Session

from constants import path
from diff.file_diff import get_diff
from models.diff import DiffHunk
from models.gerrit import ChangeData, DiffData, MetaData, Revision, FileData, MetaDataWithFile
from utils.diff_handler import DiffDataHandler
from utils.file_processor import base64_encode, dump_to_json, load_from_json
from utils.lang_identifiyer import identify_lang_from_file

# データベースモジュールのインポート
from database.database import engine, create_db_and_tables
from database.crud import create_file_data


class OpenStackAnalyzer:
    def __init__(
        self, user_name: str, token: str, start_date: datetime | None = None, end_date: datetime | None = None,
        use_db: bool = True
    ):
        self.user_name = user_name
        self.token = token
        self.headers = self._build_headers(user_name, token)
        self.base_url = "https://review.opendev.org/a"
        self.start_date = start_date
        self.end_date = end_date
        self.use_db = use_db

        # データベースとテーブルの初期化
        if self.use_db:
            create_db_and_tables()

    def _build_headers(self, user_name: str, token: str):
        credentials = f"{user_name}:{token}"
        return {
            "Authorization": f"Basic {base64_encode(credentials)}",
            "Accept": "application/json",
        }

    def _get_request(self, endpoint: str, params: dict | None = None) -> list | str:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            time.sleep(1)

            content_type = response.headers.get("Content-Type", "")

            if "application/json" in content_type:
                # JSONレスポンス
                return json.loads(response.text.replace(")]}'", ""))
            else:
                # JSONでない場合（Base64エンコードされたファイル内容等）
                # そのままテキストとして返す
                return response.text

        except requests.exceptions.HTTPError as http_err:
            raise http_err
        except Exception as e:
            raise e

    def _fetch_changes(
        self, owner: str, repo: str, page: int, status: str = "merged"
    ) -> Generator[ChangeData, None, None]:
        LIMIT = 100
        endpoint = f"/changes/"

        query = f"project:{owner}/{repo} status:{status}"
        # 期間を指定する場合
        if self.start_date and self.end_date:
            start_date_str = self.start_date.strftime("%Y-%m-%d")
            end_date_str = self.end_date.strftime("%Y-%m-%d")
            query += f" after:{start_date_str} before:{end_date_str}"
        elif self.start_date:
            start_date_str = self.start_date.strftime("%Y-%m-%d")
            query += f" after:{start_date_str}"
        elif self.end_date:
            end_date_str = self.end_date.strftime("%Y-%m-%d")
            query += f" before:{end_date_str}"

        params = {
            "q": query,
            "n": LIMIT,
            "start": (page - 1) * LIMIT,
            "o": ["ALL_REVISIONS", "ALL_COMMITS", "ALL_FILES"],
        }

        print(f"fetching from {endpoint}, page: {page}, query: {query}")
        changes = self._get_request(endpoint, params)

        if not changes:
            return

        if isinstance(changes, list):
            for change in changes:
                sorted_revisions = sorted(
                    change.get("revisions", {}).items(),
                    key=lambda x: x[1]["created"],
                )
                # 各リビジョンの情報を作成
                revisions: list[Revision] = []
                changed_files = set()
                for revision_sha, revision in sorted_revisions:
                    changed_file = list(revision.get("files", {}).keys())
                    changed_files.update(changed_file)
                    revision = change["revisions"][revision_sha]
                    revisions.append(
                        Revision(
                            hash=revision_sha,
                            committer=revision["commit"]["committer"]["name"],
                            subject=revision["commit"]["subject"],
                            commit_message=revision["commit"]["message"],
                            changed_files=changed_file,
                        )
                    )

                yield ChangeData(
                    change_id=change["change_id"],
                    branch=change["branch"],
                    merged_at=datetime.strptime(change["submitted"].split(".")[0], "%Y-%m-%d %H:%M:%S"),
                    revisions=revisions,
                )


    def get_all_changes(self, owner: str, repo: str) -> None:
        page = 1
        while True:
            changes = list(self._fetch_changes(owner, repo, page))
            if not changes:
                break
            for change in changes:
                file_changes = defaultdict(list)
                for revision in change.revisions:
                    # ファイルごとのコミットハッシュを特定
                    for file in revision.changed_files:
                        file_changes[file].append(revision.hash)

                # 各ファイルに2つのコミットがないものを除外
                file_changes = {file: hashes for file, hashes in file_changes.items() if len(hashes) >= 2}

                # 対象ファイルを保存
                for file_name, hashes in file_changes.items():
                    try:
                        if identify_lang_from_file(file_name) != "Python":
                            continue

                        # 変更前と変更後のファイルを取得
                        base_file = self._fetch_changed_file(
                            owner, repo, change.branch, change.change_id, hashes[0], file_name
                        )
                        target_file = self._fetch_changed_file(
                            owner, repo, change.branch, change.change_id, hashes[-1], file_name
                        )
                        if base_file == None or target_file == None:
                            continue

                        # 変更前と変更後のファイルを保存
                        output_path = self._create_save_path_per_year(owner) / change.change_id
                        if not output_path.exists():
                            output_path.mkdir(parents=True, exist_ok=True)

                        with open(output_path / f"{hashes[0]}.py", "w") as f:
                            f.write(base_file)
                        with open(output_path / f"{hashes[-1]}.py", "w") as f:
                            f.write(target_file)

                        # DBに取得したコミット情報を保存
                        self._store_file_revision_data(change, file_name, hashes, output_path)
                    except ValueError:
                        continue
            page += 1

    # DBに取得したコミット情報を保存
    def _store_file_revision_data(self,change: ChangeData, file_name: str, hashes: list[str], saved_path: Path) -> None:
        # ハッシュをキーにした辞書を作成
        revision_dict = {revision.hash: revision for revision in change.revisions}
        # 対応するリビジョン情報を取得
        base_revision = revision_dict[hashes[0]]
        target_revision = revision_dict[hashes[-1]]

        # コミット情報の作成
        new_file_data = FileData(
            change_id=change.change_id,
            branch=change.branch,
            file_name=file_name,
            merged_at=change.merged_at,
            base=MetaDataWithFile(
                hash=hashes[0],
                file_path=f"{saved_path}/{hashes[0]}.py",
                committer=base_revision.committer,
                subject=base_revision.subject,
                commit_message=base_revision.commit_message,
            ),
            target=MetaDataWithFile(
                hash=hashes[-1],
                file_path=f"{saved_path}/{hashes[-1]}.py",
                committer=target_revision.committer,
                subject=target_revision.subject,
                commit_message=target_revision.commit_message,
            ),
        )

        # データベースへ保存
        try:
            with Session(engine) as db:
                create_file_data(db, new_file_data)
                print(f"データベースに保存しました: {change.change_id}, {file_name}")
        except Exception as e:
            print(f"データベースへの保存中にエラーが発生しました: {e}")

    def _create_save_path_per_year(self, owner: str) -> Path:
        base_path = path.RESOURCE / owner

        start_year = self.start_date.year if self.start_date else ""
        end_year = self.end_date.year if self.end_date else ""

        if start_year and end_year:
            year_part = f"{start_year}to{end_year}"
        elif start_year:
            year_part = f"from{start_year}"
        elif end_year:
            year_part = f"to{end_year}"
        else:
            year_part = ""

        # パスを構築
        return base_path / year_part

    # 変更前と変更後のdiffを対象期間で全て取得
    def get_all_diff(self, owner: str, repo: str) -> None:
        page = 1
        while True:
            changes = list(self._fetch_changes(owner, repo, page))  # ジェネレーターをリストに変換
            if not changes:
                break
            for change in changes:
                file_changes = defaultdict(list)
                for revision in change.revisions:
                    # ファイルごとのコミットハッシュを特定
                    for file in revision.changed_files:
                        file_changes[file].append(revision.hash)

                # 各ファイルに2つのコミットがないものを除外
                file_changes = {file: hashes for file, hashes in file_changes.items() if len(hashes) >= 2}

                # ファイルごとのdiffを取得
                print(f"getting diffs...")
                for file_name, hashes in file_changes.items():
                    try:
                        if identify_lang_from_file(file_name) != "Python":
                            continue

                        # 変更前と変更後のファイルを取得
                        base_file = self._fetch_changed_file(
                            owner, repo, change.branch, change.change_id, hashes[0], file_name
                        )
                        target_file = self._fetch_changed_file(
                            owner, repo, change.branch, change.change_id, hashes[-1], file_name
                        )
                        if base_file == None or target_file == None:
                            continue

                        diffs = get_diff(base_file, target_file)

                        self._save_to_json_for_diff(change, file_name, hashes, diffs)
                    except ValueError:
                        continue

            page += 1

    def _fetch_changed_file(
        self, owner: str, repo: str, branch: str, changed_id: str, revision_id: str, file_name: str
    ) -> str | None:
        file_id = quote(file_name, safe="")
        project_id = quote(f"{owner}/{repo}", safe="")
        branch_id = quote(branch, safe="")
        endpoint = f"/changes/{project_id}~{branch_id}~{changed_id}/revisions/{revision_id}/files/{file_id}/content"
        try:
            response = self._get_request(endpoint)
            if isinstance(response, str):
                return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"404: {file_name}")
                print(f"endpoint: {endpoint}")
                return
            else:
                raise
        except Exception as e:
            raise e

    def _save_to_json_for_diff(self, change: ChangeData, file_name: str, hashes: list[str], diffs: list[DiffHunk]) -> None:
        diff_data = []
        Dh = DiffDataHandler
        # ハッシュをキーにした辞書を作成
        revision_dict = {revision.hash: revision for revision in change.revisions}
        # 対応するリビジョン情報を取得
        base_revision = revision_dict[hashes[0]]
        target_revision = revision_dict[hashes[-1]]

        for diff in diffs:
            diff_data.append(
                DiffData(
                    change_id=change.change_id,
                    branch=change.branch,
                    file_name=file_name,
                    merged_at=change.merged_at,
                    diff_hunk=DiffHunk(diff.condition, diff.consequent),
                    base=MetaData(
                        hash=hashes[0],
                        committer=base_revision.committer,
                        subject=base_revision.subject,
                        commit_message=base_revision.commit_message,
                    ),
                    target=MetaData(
                        hash=hashes[-1],
                        committer=target_revision.committer,
                        subject=target_revision.subject,
                        commit_message=target_revision.commit_message,
                    ),
                )
            )

        # 成功したPRデータを保存
        output_path = self._create_save_path(owner, repo)

        if not output_path.parent.exists():
            output_path.parent.mkdir()

        Dh.dump_to_json(diff_data, output_path)

    def _create_save_path(self, owner: str, repo: str) -> Path:
        base_path = path.RESOURCE / owner

        start_year = self.start_date.year if self.start_date else ""
        end_year = self.end_date.year if self.end_date else ""

        if start_year and end_year:
            year_part = f"{start_year}to{end_year}"
        elif start_year:
            year_part = f"from{start_year}"
        elif end_year:
            year_part = f"to{end_year}"
        else:
            year_part = ""

        # パスを構築
        return base_path / year_part / f"{repo}.json"


if __name__ == "__main__":
    owner = "openstack"
    # repos = ["neutron", "cinder", "keystone", "swift", "glance"]
    repos = ["nova"]
    load_dotenv()
    username = os.getenv("USER_NAME")
    token = os.getenv("OPENSTACK_TOKEN")
    use_db = True  # データベースを使用するフラグ
    start_year = 2013
    end_year = 2025
    for year in reversed(range(start_year, end_year)):
        for repo in repos:
            if username != None and token != None:
                # 期間を指定
                start_date = datetime(year, 1, 1)
                end_date = datetime(year + 1, 1, 1)
                OSA = OpenStackAnalyzer(username, token, start_date, end_date, use_db=use_db)
                # ジェネレーターをリストに変換
                OSA.get_all_changes(owner, repo)
    print("end")
