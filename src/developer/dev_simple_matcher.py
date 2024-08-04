import csv
from itertools import combinations
from utils.file_processor import list_files_in_directory, extract_project_name, load_from_json
from constants import path

def calc_dev_match_rate(dev1, dev2):
    """2つのプロジェクトの開発者の一致率を計算

    Args:
        dev1 (set): 1つ目の開発者の集合
        dev2 (set): 2つ目の開発者の集合

    Returns:
        float: 一致率
    """
    intersection = dev1 & dev2
    union = dev1 | dev2

    if len(union) == 0:
        return 0.0

    return round((len(intersection) / len(union)), 2)

if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/dev/{owner}"
    projects = list_files_in_directory(dir_path)
    project_names = [extract_project_name(proj) for proj in projects]

    # 類似度を保存するための行列を初期化
    similarity_matrix = [[0.0 for _ in range(len(projects))] for _ in range(len(projects))]
    project_indices = {project: idx for idx, project in enumerate(projects)}

    for proj1, proj2 in combinations(projects, 2):
        dev1 = set(load_from_json(f"{dir_path}/{proj1}").keys())
        dev2 = set(load_from_json(f"{dir_path}/{proj2}").keys())

        similarity = calc_dev_match_rate(dev1, dev2)
        idx1 = project_indices[proj1]
        idx2 = project_indices[proj2]
        similarity_matrix[idx1][idx2] = similarity
        similarity_matrix[idx2][idx1] = similarity

    # CSVファイルに行列として出力
    csv_path = f"{path.RESULTS}/{owner}/dev_simple_match_rate_matrix.csv"
    with open(csv_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        header = [""] + project_names
        writer.writerow(header)
        for i, project in enumerate(project_names):
            row = [project] + similarity_matrix[i]
            writer.writerow(row)

    print(f"Developer match rate matrix saved to {csv_path}")
