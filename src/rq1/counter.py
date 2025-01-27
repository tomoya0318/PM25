from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from itertools import islice, combinations
from tqdm import tqdm

from constants import path
from pattern.prefix_span import PrefixSpan
from pattern.diff2sequence import compute_token_diff, extract_diff


def create_combination(sequence):
    n = len(sequence)

    for r in range(2, min((n + 1), 10) + 1):
        for comb in combinations(sequence, r):
            yield comb


def add_combination(sequences: set, combinations: set):
    for sequence in sequences:
        combinations.add(create_combination(sequence))
    return len(combinations)

def load_token_diff(diff_path: Path, save_path: Path):
    BATCH_SIZE = 10

    combinations = set()
    total_diffs = 0
    diff_counts = []  # 読み込んだ diff の数
    pattern_counts = []  # 作成されたパターンの数

    generator = extract_diff(diff_path)
    while True:
        batch = list(islice(generator, BATCH_SIZE))
        diffs = set()
        if not batch:
            break

        for merged_at, language, diff_hunk in batch:
            token_diff = compute_token_diff(language, diff_hunk)
            print(token_diff)
            diffs.add(tuple(token_diff))

        print(diffs)
        # 現在の累積 diff 数と生成されたパターン数を取得
        total_diffs += BATCH_SIZE

        for sequence in tqdm(diffs):
            for comb in create_combination(sequence):
                combinations.add(comb)

        diff_counts.append(total_diffs)
        pattern_counts.append(len(combinations))

        print(f"読み込んだdiffの数: {total_diffs}, 作成されたパターン数: {len(combinations)}")

    # グラフ描画
    plt.figure(figsize=(10, 6))
    plt.plot(diff_counts, pattern_counts, marker='o', linestyle='-', color='b')
    plt.xlabel('diff')
    plt.ylabel('created pattern')
    plt.title('')
    plt.grid(True)
    plt.savefig(save_path)

# 関数の呼び出し例
diff_path = path.RESOURCE/"openstack"/"2013to2014"/"neutron.json"  # JSONファイルのパスを指定
save_path = path.RESULTS/"openstack.png"
load_token_diff(diff_path, save_path)
