import json
import os
import subprocess
import uuid

from dataclasses import dataclass, field

from constants import path
from utils.file_processor import remove_dir


@dataclass
class Match:
    src: str
    dest: str


@dataclass
class Action:
    action: str
    tree: str
    parent: str | None
    at: int | None
    label: str | None


@dataclass
class GumTreeResponse:
    matches: list[Match] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)


def run_GumTree(src_code: str, dest_code: str) -> str:
    id: str = str(uuid.uuid4())
    TMP_DIR = os.path.join(path.TMP, id)
    try:
        os.makedirs(TMP_DIR, exist_ok=True)
        print(f"Directory '{TMP_DIR}' created or already exists.")
    except OSError as e:
        raise OSError(f"Failed to create directory: {str(e)}")

    # 一旦pythonのみ対応，のちに多言語？
    src_path = os.path.join(TMP_DIR, "src.py")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write(src_code)
    dest_path = os.path.join(TMP_DIR, "dest.py")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(dest_code)

    # dockerコンテナ内でgumtreeを処理させる用
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{TMP_DIR}:/tmp/{id}",
        "tomoya0318/gumtree",
        "gumtree",
        "textdiff",
        "-f",
        "JSON",
        f"/tmp/{id}/src.py",
        f"/tmp/{id}/dest.py",
    ]

    try:
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        response = json.loads(output.stdout)
        return json.dumps(response, indent=2)
    except subprocess.CalledProcessError as e:
        raise subprocess.SubprocessError(f"Command execution failed: {e.stderr}")
    finally:
        remove_dir(TMP_DIR)


if __name__ == "__main__":
    condition = "cts.cancel()\ncts.dispose()"
    consequent = "cts.cancel(true)"

    output = run_GumTree(condition, consequent)
    output_path = os.path.join(path.RESULTS, "sample", "gumtree_result.json")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
