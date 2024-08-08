import polars as pl
from utils.file_processor import count_elements_in_json, list_files_in_directory, extract_project_name
from constants import path


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/pattern/{owner}"
    projects = list_files_in_directory(dir_path)

    project_names = [extract_project_name(proj, owner) for proj in projects]
    element_counts = []

    for project in projects:
        file_path = f"{dir_path}/{project}"
        num_elements = count_elements_in_json(file_path)
        element_counts.append(num_elements)

    # polars DataFrameに変換
    df = pl.DataFrame({"project": project_names, "elements": element_counts})

    # CSVファイルに出力
    csv_path = f"{path.RESULTS}/{owner}/pattern_element_counts.csv"
    df.write_csv(csv_path)

    print(f"Element counts saved to {csv_path}")
