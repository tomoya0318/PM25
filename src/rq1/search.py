import os
from pathlib import Path

from git import Repo
from constants import path
from pattern.confidence import is_actually_change, is_trigger_sequence
from utils.discord import send_discord_notification
from fetch.git import checkout_commit, clone_project


def search_pattern_in_repo(repo_path: Path, pattern: list[str]) -> None:
    trigger_count = 0
    actually_changed_count = 0
    for root, _, file_name in os.walk(repo_path):
        for file in file_name:
            file_path = Path(root) / file
            if file.endswith(".py"):
                with open(file_path, "r") as f:
                    for line in f:
                        if is_trigger_sequence(pattern, line):
                            trigger_count += 1
                        if is_actually_change(pattern, line):
                            actually_changed_count += 1

    print(f"trigger:{trigger_count}, acutually:{actually_changed_count}")

if __name__ == "__main__":
    pattern = pattern = [
        "-str",
        "-(",
        "-uuid",
        "+uuidutils",
        "=.",
        "-uuid4",
        "+generate_uuid",
        "=(",
        "=)",
        "-)"
    ]
    repo_path = path.TMP / "nova"
    revisions = ["82636d678883788c3781164e3453b58bfa0661cf", "39cac35bdd1a30dddf9912fe7235a8405792170b", "38a8a142a3663d9f4b15d90264fcf9f835937087", "26521718bdba3bccbf6270e26b76754c26304658", "972218e6ae0af4de565b8b1e41a20c4db13b9e7d", "ef7598ac2896d08a89e50ccb82a47244e63d6248", "50bf252250a35f7d9d09c75243f80a4ec0a0fc39", "e667a7f8d807f5c2e8d3137eed91072881adb793", "12ca930e459ce2b5487f8d2f9854069ed9d95cf1"]
    for revision in revisions:
        print(f"Checking out {revision}\n")
        checkout_commit(Repo(repo_path), revision)
        search_pattern_in_repo(repo_path, pattern)
    send_discord_notification("Search finished")