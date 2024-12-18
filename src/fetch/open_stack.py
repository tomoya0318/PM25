from datetime import datetime
import json
import os
import time

from collections import defaultdict
from dotenv import load_dotenv
from typing import Generator
from urllib.parse import quote
import requests

from constants import path
from diff.file_diff import get_diff
from models.diff import DiffHunk
from models.gerrit import ChangeData, DiffData, MetaData, Revision
from utils.diff_handler import DiffDataHandler
from utils.file_processor import base64_encode
from utils.lang_identifiyer import identify_lang_from_file


class OpenStackAnalyzer:
    def __init__(
        self, user_name: str, token: str, start_date: datetime | None = None, end_date: datetime | None = None
    ):
        self.user_name = user_name
        self.token = token
        self.headers = self._build_headers(user_name, token)
        self.base_url = "https://review.opendev.org/a"
        self.start_date = start_date
        self.end_date = end_date

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
                merged_at = datetime.strptime(change["submitted"].split(".")[0], "%Y-%m-%d %H:%M:%S")
                sorted_revisions = sorted(
                    change.get("revisions", {}).items(),
                    key=lambda x: x[1].get("created", "9999-12-31 23:59:59.000000000"),
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

                yield ChangeData(change_id=change["change_id"], merged_at=merged_at, revisions=revisions)

    def get_all_diff(self, owner: str, repo: str) -> None:
        page = 1
        while True:
            changes = self._fetch_changes(owner, repo, page)
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
                        base_file = self._fetch_changed_file(change.change_id, hashes[0], file_name)
                        target_file = self._fetch_changed_file(change.change_id, hashes[-1], file_name)
                        if base_file == None or target_file == None:
                            continue

                        diffs = get_diff(base_file, target_file)

                        self._save_to_json(change, file_name, hashes, diffs)
                    except ValueError as e:
                        print(e)
                        continue

            page += 1

    def _fetch_changed_file(self, changed_id: str, revision_id: str, file_name: str) -> str | None:
        file_id = quote(file_name, safe="")
        endpoint = f"/changes/{changed_id}/revisions/{revision_id}/files/{file_id}/content"
        try:
            response = self._get_request(endpoint)
            if isinstance(response, str):
                return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"404: {file_name}")
                return
            else:
                raise
        except Exception as e:
            raise e

    def _save_to_json(self, change: ChangeData, file_name: str, hashes: list[str], diffs: list[DiffHunk]) -> None:
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
        output_path = path.RESOURCE / owner / f"{repo}.json"
        if not output_path.parent.exists():
            output_path.parent.mkdir()
        Dh.dump_to_json(diff_data, output_path, owner, repo)


if __name__ == "__main__":
    owner = "openstack"
    repo = "nova"
    load_dotenv()
    username = os.getenv("USER_NAME")
    token = os.getenv("OPENSTACK_TOKEN")
    output_path = path.RESOURCE / owner / f"{repo}.json"
    if output_path.exists():
        output_path.unlink()
        print(f"{output_path}を削除しました")
    if username != None and token != None:
        # 期間を指定
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 1, 1)
        OSA = OpenStackAnalyzer(username, token, start_date, end_date)
        # OSA._fetch_changed_file("Ia600ceb22c5939117095593b97ed94735c8f953c", "cfc6f69cc2d513f09cc002a571554f9d8dd08e9f", "nova/virt/libvirt/utils.py")
        # # ジェネレーターをリストに変換
        OSA.get_all_diff(owner, repo)
