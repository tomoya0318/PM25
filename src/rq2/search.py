import os
from pathlib import Path

import japanize_matplotlib
import matplotlib.pyplot as plt
from git import Repo
from constants import path
from pattern.confidence import is_actually_change, is_trigger_sequence
from utils.discord import send_discord_notification
from fetch.git import checkout_commit, clone_project

def search_pattern_in_repo(repo_path: Path, pattern: list[str]) -> tuple[int, int]:
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
    return trigger_count, actually_changed_count

def main():
    pattern = [
        "-str", "-(", "-uuid", "+uuidutils", "=.",
        "-uuid4", "+generate_uuid", "=(", "=)", "-)"
    ]
    repo_path = path.TMP / "nova"

    revisions = {
        2016: "82636d678883788c3781164e3453b58bfa0661cf",
        2017: "39cac35bdd1a30dddf9912fe7235a8405792170b",
        2018: "38a8a142a3663d9f4b15d90264fcf9f835937087",
        2019: "26521718bdba3bccbf6270e26b76754c26304658",
        2020: "972218e6ae0af4de565b8b1e41a20c4db13b9e7d",
        2021: "ef7598ac2896d08a89e50ccb82a47244e63d6248",
        2022: "50bf252250a35f7d9d09c75243f80a4ec0a0fc39",
        2023: "e667a7f8d807f5c2e8d3137eed91072881adb793",
        2024: "12ca930e459ce2b5487f8d2f9854069ed9d95cf1"
    }
    # データ収集
    triggers = []
    actuals = []
    years = []

    # 年号でソートして処理
    for year in sorted(revisions.keys()):
        commit_hash = revisions[year]
        print(f"Checking out {year} ({commit_hash[:7]})")
        checkout_commit(Repo(repo_path), commit_hash)
        trigger, actually = search_pattern_in_repo(repo_path, pattern)

        triggers.append(trigger)
        actuals.append(actually)
        years.append(str(year))  # 文字列に変換

    # グラフ描画
    plt.figure(figsize=(12, 6))

    bar_width = 0.6
    indices = range(len(years))

    # 積み上げ棒グラフ
    plt.bar(indices, triggers, width=bar_width, label='変更前のソースコード', color='#1f77b4')
    plt.bar(indices, actuals, width=bar_width, bottom=triggers, label='変更後のソースコード', color='#ff7f0e')

    # グラフの装飾
    pattern_title = "Pattern:\n" + " ".join([
        f"'{p}'" for p in pattern
    ])
    plt.title(pattern_title, fontsize=10, pad=20)
    # plt.xlabel('年')
    plt.ylabel('出現回数')
    plt.xticks(indices, years, rotation=45, ha='right')  # 年号をラベルに使用
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    plt.savefig('yearly_analysis.png')
    print("グラフを yearly_analysis.png に保存しました")

if __name__ == "__main__":
    main()