import json

from pathlib import Path

from models.gerrit import DiffData


#将来的にデータベースに移行
class DiffDataHandler:
    @staticmethod
    def load_from_json(file_path: Path) -> list[DiffData]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            return [DiffData.from_dict(item) for item in data]

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON format: {str(e)}", e.doc, e.pos)
        except KeyError as e:
            raise KeyError(f"Missing required key in JSON: {str(e)}")

    @staticmethod
    def dump_to_json(data: list[DiffData], output_path: Path) -> None:
        if output_path.exists():
            diffs = DiffDataHandler.load_from_json(output_path)
        else:
            # ディレクトリ作成
            output_path.parent.mkdir(parents=True, exist_ok=True)
            diffs = []

        # 新しいデータを追加
        diffs.extend(data)
        diffs_dict = [d.to_dict() for d in diffs]

        # ファイルに保存
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(diffs_dict, f, indent=4, ensure_ascii=False)
            print(f"Appended diffs to {output_path}")
        except OSError as e:
            raise OSError(f"Failed to save file: {str(e)}")

