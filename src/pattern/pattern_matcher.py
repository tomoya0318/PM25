import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from constants import path
from utils.file_processor import load_from_json, extract_project_name
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns


def calc_pattern_match_rate(patterns1, patterns2):
    """パターンの一致度を計算

    Args:
        patterns1 (dict): 最初のプロジェクトのパターン
        patterns2 (dict): 2つ目のプロジェクトのパターン

    Returns:
        float: 一致度（Jaccard類似度）
    """
    patterns1_set = set(tuple(item["pattern"]) for item in patterns1)
    patterns2_set = set(tuple(item["pattern"]) for item in patterns2)

    intersection = patterns1_set & patterns2_set
    union = patterns1_set | patterns2_set

    if len(union) == 0:
        return 0.0

    return round((len(intersection) / len(union)), 3)


def filter_patterns_by_support(patterns, min_support):
    """指定されたサポート値以上のパターンをフィルタリングする

    Args:
        patterns (list): パターンのリスト
        min_support (int): 最小サポート値

    Returns:
        list: フィルタリングされたパターンのリスト
    """
    return [pattern for pattern in patterns if pattern["support"] >= min_support]


def calculate_match_rate(min_support2, filtered_patterns1, patterns2):
    """パターン一致度を計算する

    Args:
        min_support2 (int): 2つ目のプロジェクトの最小サポート値
        filtered_patterns1 (list): 最初のプロジェクトのフィルタリングされたパターン
        patterns2 (list): 2つ目のプロジェクトのパターン

    Returns:
        tuple: (min_support2, 一致度)
    """
    filtered_patterns2 = filter_patterns_by_support(patterns2, min_support2)
    return min_support2, calc_pattern_match_rate(filtered_patterns1, filtered_patterns2)


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/pattern/{owner}"
    # projects = ["numpy_numpy_Python_master.json", "numpy_numpy-financial_Python_master.json"]
    projects = ["numpy_numpydoc_master.json", "numpy_numpy.org_Python_master.json"]
    project_name = [extract_project_name(project, owner) for project in projects]
    # "numpy_numpydoc_Python_master.json"

    support_values = range(2, 21, 2)  # support値の範囲
    heatmap_data = np.zeros((len(support_values), len(support_values)))

    for index, proj1 in enumerate(projects[:-1]):
        print(f"loading {proj1}")
        patterns1 = load_from_json(f"{dir_path}/{proj1}")
        for proj2 in projects[index:]:
            print(f"loading {proj2}")
            patterns2 = load_from_json(f"{dir_path}/{proj2}")
            for min_support1 in tqdm(support_values, desc="support1", leave=False):
                filtered_patterns1 = filter_patterns_by_support(patterns1, min_support1)
                with ProcessPoolExecutor() as executor:
                    futures = {
                        executor.submit(
                            calculate_match_rate, min_support2, filtered_patterns1, patterns2
                        ): min_support2
                        for min_support2 in support_values
                    }

                    # tqdmを使用してプログレスバーを作成
                    for future in tqdm(
                        as_completed(futures), total=len(futures), desc="Calculating match rates", leave=False
                    ):
                        min_support2 = futures[future]
                        try:
                            match_rate = future.result()[1]
                            # 累積せず直接代入
                            heatmap_data[support_values.index(min_support1), support_values.index(min_support2)] = (
                                match_rate
                            )

                        except Exception as e:
                            print(f"Error calculating match rate: {e}")

    # ヒートマップを描画
    print("make heatmap...")
    plt.figure(figsize=(10, 8))
    # データの行を逆順にする
    print(heatmap_data)
    reversed_heatmap_data = heatmap_data[::-1]

    sns.heatmap(
        reversed_heatmap_data,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        xticklabels=support_values,
        yticklabels=list(reversed(support_values)),  # Y軸ラベルも逆順に設定
        vmin=0,
        vmax=1.0,
    )
    plt.xlabel(project_name[1])
    plt.ylabel(project_name[0])

    # 保存先を指定してヒートマップを保存
    save_path = f"{path.RESULTS}/{owner}/{project_name[0]}_{project_name[1]}_pattern_match_rates_heatmap.png"
    plt.savefig(save_path)

    # projects = ["numpy_numpy_Python_master.json", "numpy_numpy.org_Python_master.json"]
    projects = ["numpy_numpy_Python_master.json", "numpy_numpy-vendor_Python_master.json"]
    # projects = ["numpy_numpy_Python_master.json", "numpy_numpy-refactor_Python_master.json"]
    # projects = ["numpy_numpy_Python_master.json", "numpy_numpy-financial_Python_master.json"]
    # projects = ["numpy_numpy_Python_master.json", "numpy_numpydoc_Python_master.json"]
    # projects = ["numpy_numpy-financial_Python_master.json", "numpy_numpy.org_Python_master.json"]
    # projects = ["numpy_numpy-financial_Python_master.json", "numpy_numpy-refactor_Python_master.json"]
    # projects = ["numpy_numpydoc_Python_master.json", "numpy_numpy.org_Python_master.json"]
    # projects = ["numpy_numpydoc_Python_master.json", "numpy_numpy-refactor_Python_master.json"]
    # projects = ["numpy_numpydoc_Python_master.json", "numpy_numpy-financial_Python_master.json"]
