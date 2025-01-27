import json
import os
import subprocess
import uuid

from constants import path
from models.gumtree import Action, Match, GumTreeResponse
from utils.file_processor import remove_dir


def run_GumTree(src_code: list, dest_code: list) -> GumTreeResponse:
    id: str = str(uuid.uuid4())
    TMP_DIR = path.TMP/id

    try:
        os.makedirs(TMP_DIR, exist_ok=True)
        print(f"Directory '{TMP_DIR}' created")

        # 一旦pythonのみ対応，のちに多言語？
        src_path = TMP_DIR/"src.py"
        with open(src_path, "w", encoding="utf-8") as f:
            f.write("\n".join(src_code))
        dest_path = TMP_DIR/"dest.py"
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write("\n".join(dest_code))

        command = [
            "gumtree",
            "textdiff",
            "-f",
            "JSON",
            src_path,
            dest_path
        ]

        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        response_dict = json.loads(output.stdout)
        return GumTreeResponse(
            matches=[Match(**match) for match in response_dict.get("matches", [])],
            actions=[Action(**action) for action in response_dict.get("actions", [])],
        )

    except OSError as e:
        raise OSError(f"Failed to create directory: {str(e)}")

    except subprocess.CalledProcessError as e:
        raise subprocess.SubprocessError(f"Docker command failed: {e.stderr}")

    finally:
        remove_dir(TMP_DIR)

if __name__ == "__main__":
    condition = ['@exception.wrap_exception(notifier=notifier, publisher_id=publisher_id())']
    consequent = ["@wrap_exception()"]
    response = run_GumTree(condition, consequent)
    print(response)