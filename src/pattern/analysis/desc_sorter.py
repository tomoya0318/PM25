from constants import path
from utils.file_processor import load_from_json, list_files_in_directory, dump_to_json


def sort_desc(data: dict):
    return sorted(data, key=lambda x: x["support"], reverse=True)


def main():
    dir_path = f"{path.INTERMEDIATE}/pattern"
    out_path = f"{dir_path}/desc"
    projects = list_files_in_directory(f"{dir_path}/numpy")

    for project in projects:
        data = load_from_json(f"{dir_path}/numpy/{project}")
        sorted_data = sort_desc(data)
        dump_to_json(sorted_data, f"{out_path}/{project}")


if __name__ == "__main__":
    main()
    print("end")
