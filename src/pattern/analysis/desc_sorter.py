from constants import path
from utils.file_processor import load_from_json, list_files_in_directory, dump_to_json


def sort_desc(data: dict):
    return sorted(data, key=lambda x: x["support"], reverse=True)


def main():
    owner = "openstack"
    dir_path = path.RESULTS / owner / "all" / "filtered_nova.json"
    data = load_from_json(dir_path)
    sorted_data = sort_desc(data)
    dump_to_json(sorted_data, dir_path)


if __name__ == "__main__":
    main()
    print("end")
