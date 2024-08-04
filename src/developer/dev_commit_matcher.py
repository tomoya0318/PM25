import csv
import numpy as np
from itertools import combinations
from utils.file_processor import load_from_json, list_files_in_directory
from constants import path
from sklearn.metrics.pairwise import cosine_similarity


def calc_dev_match_rate(vec1, vec2):
    """2つのプロジェクトの開発者の活動量（コミット数）を考慮した一致率を計算

    Args:
        vec1 (list): 1つ目の開発者のベクトル（出現数）
        vec2 (list): 2つ目の開発者のベクトル（出現数）

    Returns:
        float: コサイン類似度
    """
    if not vec1 or not vec2:
        return None

    vec1 = np.array(vec1).reshape(1, -1)
    vec2 = np.array(vec2).reshape(1, -1)

    similarity = cosine_similarity(vec1, vec2)[0][0]
    return round(similarity, 2)


def create_commit_vector(authors, all_authors):
    return [authors.get(author, 0) for author in all_authors]


def extract_project_name(project_filename):
    """プロジェクトのファイル名からプロジェクト名を抽出する

    Args:
        project_filename (str): プロジェクトのファイル名

    Returns:
        str: 抽出されたプロジェクト名
    """
    return project_filename.split("_")[1]


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/dev/{owner}"
    projects = list_files_in_directory(dir_path)
    project_names = [extract_project_name(proj) for proj in projects]

    # コサイン類似度を保存するための行列を初期化
    similarity_matrix = np.zeros((len(projects), len(projects)))
    project_indices = {project: idx for idx, project in enumerate(projects)}

    for proj1, proj2 in combinations(projects, 2):
        dev1 = load_from_json(f"{dir_path}/{proj1}")
        dev2 = load_from_json(f"{dir_path}/{proj2}")
        all_authors = set(dev1.keys()).union(set(dev2.keys()))

        vec1 = create_commit_vector(dev1, all_authors)
        vec2 = create_commit_vector(dev2, all_authors)

        similarity = calc_dev_match_rate(vec1, vec2)
        if similarity is not None:
            idx1 = project_indices[proj1]
            idx2 = project_indices[proj2]
            similarity_matrix[idx1, idx2] = similarity
            similarity_matrix[idx2, idx1] = similarity

    # CSVファイルに行列として出力
    csv_path = f"{path.RESULTS}/{owner}/dev_cosine_sim_matrix.csv"
    with open(csv_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        header = [""] + project_names
        writer.writerow(header)
        for i, project in enumerate(project_names):
            row = [project] + similarity_matrix[i].tolist()
            writer.writerow(row)

    print(f"Cosine similarity matrix saved to {csv_path}")
