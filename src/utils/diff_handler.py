import json
from datetime import datetime

from dataclasses import asdict
from pathlib import Path
from typing import Generator

from models.diff import DiffData, DiffHunk


class DiffDataHandler:
    @staticmethod
    def load_from_json(file_path: Path) -> Generator[DiffData, None, None]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for diff in data["diffs"]:
                # DiffHunkの作成
                diff_hunk = DiffHunk(
                    condition=diff["diff_hunk"]["condition"], consequent=diff["diff_hunk"]["consequent"]
                )

                # DiffDataの作成
                diff_data = DiffData(
                    file_name=diff["file_name"],
                    pr_number=diff["pr_number"],
                    base_hash=diff["base_hash"],
                    target_hash=diff["target_hash"],
                    diff_hunk=diff_hunk,
                    merged_date=datetime.fromisoformat(diff["merged_date"]),
                    base_message=diff["base_message"],
                    target_message=diff["target_message"],
                )
                yield diff_data

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON format: {str(e)}", e.doc, e.pos)
        except KeyError as e:
            raise KeyError(f"Missing required key in JSON: {str(e)}")

    @staticmethod
    def dump_to_json(data: list[DiffData], output_path: Path, owner: str, repo: str) -> None:
        def custom_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()  # datetime を ISO 8601 形式の文字列に変換
            raise TypeError(f"Type {type(obj)} not serializable")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        json_data = {"repository": f"{owner}/{repo}", "diffs": [asdict(diff) for diff in data]}
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=custom_serializer)
            print(f"Saved diffs to {output_path}")
        except OSError as e:
            raise OSError(f"Failed to save file: {str(e)}")
