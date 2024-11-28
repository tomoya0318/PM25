import json
import os
import subprocess
import uuid

from constants import path
from models.gumtree import GumTreeResponse
from utils.file_processor import remove_dir


def run_GumTree(src_code: list, dest_code: list) -> GumTreeResponse:
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
        f.write("\n".join(src_code))
    dest_path = os.path.join(TMP_DIR, "dest.py")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(dest_code))

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
        return json.loads(output.stdout)
    except subprocess.CalledProcessError as e:
        raise subprocess.SubprocessError(f"Command execution failed: {e.stderr}")
    finally:
        remove_dir(TMP_DIR)


if __name__ == "__main__":
    condition = [
        "ASSERT_EQ(expected, actual);",
        "ASSERT_EQ(expected2, actual2);",
        "ASSERT_EQ(expected3, actual3);"
    ]

    consequent = [
        "EXPECT_EQ(expected, actual);",
        "EXPECT_EQ(expected2, actual2);",
        "EXPECT_EQ(expected3, actual3);"
    ]

    response = run_GumTree(condition, consequent)
    output = json.dumps(response, indent=4)
    output_path = os.path.join(path.RESULTS, "sample", "gumtree_result.json")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
