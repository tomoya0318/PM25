import polars as pl
from utils.file_processor import list_files_in_directory, extract_project_name, count_elements_in_json
from constants import path


if __name__ == "__main__":
    owner = "anaconda"
    dir_path = f"{path.INTERMEDIATE}/dev/{owner}"
    projects = list_files_in_directory(dir_path)

    project_names = [extract_project_name(proj) for proj in projects]
    element_counts = []

    for project in projects:
        file_path = f"{dir_path}/{project}"
        num_elements = count_elements_in_json(file_path)
        element_counts.append(num_elements)

    # polars DataFrameに変換
    df = pl.DataFrame({"project": project_names, "elements": element_counts})

    # CSVファイルに出力
    csv_path = f"{path.RESULTS}/{owner}/dev_element_counts.csv"
    df.write_csv(csv_path)

    print(f"Element counts saved to {csv_path}")
