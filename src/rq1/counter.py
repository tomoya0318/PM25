from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from itertools import islice

from constants import path
from pattern.prefix_span import PrefixSpan
from pattern.diff2sequence import compute_token_diff, extract_diff


def count_pattern(sequences: list) -> int:
    def _has_change_pattern(pattern: list[str]) -> bool:
        return len(pattern) > 1 and any(token.startswith(("+", "-")) for token in pattern)

    prefix_span = PrefixSpan(1)
    patterns = prefix_span.fit(sequences)

    filtered_patterns = [(pattern, support) for pattern, support in patterns if _has_change_pattern(pattern)]
    print(filtered_patterns)
    return len(filtered_patterns)

def load_token_diff(diff_path: Path, save_path: Path):
    BATCH_SIZE = 1

    diffs = []  # トークン差分のシーケンスを格納
    diff_counts = []  # 読み込んだ diff の数
    pattern_counts = []  # 作成されたパターンの数

    generator = extract_diff(diff_path)
    batch_index = 1  # バッチ番号
    while True:
        batch = list(islice(generator, BATCH_SIZE))
        if not batch:
            break

        for merged_at, language, diff_hunk in batch:
            token_diff = compute_token_diff(language, diff_hunk)
            diffs.append(token_diff)

        # 現在の累積 diff 数と生成されたパターン数を取得
        total_diffs = len(diffs)
        count = count_pattern(diffs)

        diff_counts.append(total_diffs)
        pattern_counts.append(count)

        print(f"バッチ {batch_index}: 読み込んだdiffの数: {total_diffs}, 作成されたパターン数: {count}")
        batch_index += 1

    # グラフ描画
    plt.figure(figsize=(10, 6))
    plt.plot(diff_counts, pattern_counts, marker='o', linestyle='-', color='b')
    plt.xlabel('diff')
    plt.ylabel('created pattern')
    plt.title('')
    plt.grid(True)
    plt.savefig(save_path)

# 関数の呼び出し例
diff_path = path.RESOURCE/"openstack"/"2013to2014"/"nova.json"  # JSONファイルのパスを指定
save_path = path.RESULTS/"openstack.png"
load_token_diff(diff_path, save_path)
