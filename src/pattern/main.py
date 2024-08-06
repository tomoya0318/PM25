from constants import path
from pattern.converter import process_large_patch_pairs
from pattern.source_preprocessor import extract_diff, save_patterns_to_json
from utils.file_processor import list_files_in_directory


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/train_data/{owner}"
    projects = list_files_in_directory(dir_path)
    for project in projects:
        file_path = f"{dir_path}/{project}"
        print(file_path)
        output_path = f"{path.INTERMEDIATE}/pattern/{owner}/{project}.json"
        patch_pairs = extract_diff(file_path)
        filtered_patterns = process_large_patch_pairs(patch_pairs)
        save_patterns_to_json(filtered_patterns, output_path)
