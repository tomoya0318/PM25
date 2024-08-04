import numpy as np
from itertools import combinations
from constants import path
import csv
from utils.file_processor import format_pattern, load_from_json, list_files_in_directory, extract_project_name


def calc_pattern_match_rate(pattern1, pattern2):
    intersection = pattern1 & pattern2
    union = pattern1 | pattern2

    if len(union) == 0:
        return 0.0

    return round((len(intersection) / len(union)), 3)


def format_all_pattern(patterns):
    result = set()
    for pattern in patterns:
        pattern = format_pattern(pattern)
        result.add(tuple(pattern))
    return result


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/pattern/{owner}"
    projects = list_files_in_directory(dir_path)
    project_names = [extract_project_name(proj) for proj in projects]

    # パターン一致率を保存するための行列を初期化
    match_rate_matrix = np.zeros((len(projects), len(projects)))
    project_indices = {project: idx for idx, project in enumerate(projects)}

    for proj1, proj2 in combinations(projects, 2):
        pattern1 = load_from_json(f"{dir_path}/{proj1}")
        pattern2 = load_from_json(f"{dir_path}/{proj2}")
        pattern1 = format_all_pattern(pattern1)
        pattern2 = format_all_pattern(pattern2)

        match_rate = calc_pattern_match_rate(pattern1, pattern2)
        idx1 = project_indices[proj1]
        idx2 = project_indices[proj2]
        match_rate_matrix[idx1, idx2] = match_rate
        match_rate_matrix[idx2, idx1] = match_rate

    # CSVファイルに行列として出力
    csv_path = f"{path.RESULTS}/{owner}/pattern_match_rate_matrix.csv"
    with open(csv_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        header = [""] + project_names
        writer.writerow(header)
        for i, project in enumerate(project_names):
            row = [project] + match_rate_matrix[i].tolist()
            writer.writerow(row)

    print(f"Pattern match rate matrix saved to {csv_path}")
