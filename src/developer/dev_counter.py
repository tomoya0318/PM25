import polars as pl
from utils.file_processor import list_files_in_directory, extract_project_name
from developer.author_preprocessor import extract_author
from constants import path


def count_developers_and_commits(file_path):
    authors = extract_author(file_path)
    author_count = len(authors)
    commit_count = sum(authors.values())
    return author_count, commit_count


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/train_data/ten_{owner}"
    projects = list_files_in_directory(dir_path)
    project_names = [extract_project_name(proj, owner) for proj in projects]

    developer_counts = []
    commit_counts = []

    for proj in projects:
        file_path = f"{dir_path}/{proj}"
        author_count, commit_count = count_developers_and_commits(file_path)
        developer_counts.append(author_count)
        commit_counts.append(commit_count)

    # polars DataFrameに変換
    df = pl.DataFrame({"project": project_names, "developers": developer_counts, "commits": commit_counts})

    # CSVファイルに出力
    csv_path = f"{path.RESULTS}/{owner}/dev_element_counts.csv"
    df.write_csv(csv_path)

    print(f"Element counts saved to {csv_path}")
