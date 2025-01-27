from datetime import datetime
from joblib import Parallel, delayed
import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter
import numpy as np
from pathlib import Path

from abstractor.abstraction import abstract_code
from constants import path
from models.diff import DiffHunk
from pattern.confidence import is_actually_change, is_trigger_sequence
from models.gerrit import DiffData
from utils.diff_handler import DiffDataHandler
from utils.discord import send_discord_notification


def extract_change_time(item: DiffData, pattern: list[str]) -> datetime | None:
    condition = item.diff_hunk.condition
    consequent = item.diff_hunk.consequent

    if not condition or not consequent:
        return None

    # abstracted_diff = abstract_code(DiffHunk(condition, consequent))

    if is_trigger_sequence(pattern, condition):
        if is_actually_change(pattern, consequent):
            return item.merged_at
    else:
        return None


def parallel_extract_change_time(diff_path: Path, pattern: list[str]) -> list[datetime]:
    data_list = DiffDataHandler.load_from_json(diff_path)

    merged_time_list = Parallel(n_jobs=-1, verbose=10)(
        delayed(extract_change_time)(item, pattern) for item in data_list
    )

    return list(filter(None, merged_time_list))


def plot_change_times(change_times: list[datetime]) -> None:
    # 日付ごとの変更回数をカウント
    dates = change_times
    counts = np.ones(len(dates))  # 各時点で1回の変更があったとカウント

    # プロットの作成
    plt.figure(figsize=(12, 6))
    plt.plot(dates, np.cumsum(counts), marker='o', linestyle='-', markersize=6)

    # グラフの装飾
    plt.title(f'Cumulative Changes Over Time\n{owner}/{repo}: {pattern}')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Number of Changes')

    # x軸の設定（年単位の目盛り）
    ax = plt.gca()

    start_date = datetime(2016, 1, 1)
    end_date = datetime(2025, 12, 31)
    ax.set_xlim(start_date, end_date)

    # x軸のメモリを1年ごとに設定
    ax.xaxis.set_major_locator(YearLocator(1))  # 1年ごとにメモリを表示
    ax.xaxis.set_major_formatter(DateFormatter('%Y'))

    # y軸のメモリを設定
    ax.set_ylim(0, 200)
    plt.yticks(np.arange(0, 201, 50))

    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # グラフを保存
    plt.savefig(f'{owner}_{repo}_actually_changes.png')


if __name__ == "__main__":
    owner = "openstack"
    repo = "nova"
    start_year = 2016
    end_year = 2025
    pattern = [
        "-str",
        "-(",
        "-uuid",
        "+uuidutils",
        "=.",
        "-uuid4",
        "+generate_uuid",
        "=()"
        "-)"
    ]

    change_times = []
    for year in range(start_year, end_year):
        diff_path = path.RESOURCE / owner / f"{year}to{year + 1}" / f"{repo}.json"
        change_times.extend(parallel_extract_change_time(diff_path, pattern))

    change_times.sort()
    # with open("tmp.txt", "w") as f:
    #     f.write("\n".join([str(t) for t in change_times]))

    plot_change_times(change_times)
    send_discord_notification(f"Generated change plot")
