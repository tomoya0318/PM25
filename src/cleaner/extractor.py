from datetime import datetime, timedelta
from tqdm import tqdm
from utils.file_processor import load_from_json, list_files_in_directory, dump_to_json
from constants import path

def get_oldest_date(data):
    oldest_date = None
    for item in data:
        created_at = datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S")
        if oldest_date is None or created_at < oldest_date:
            oldest_date = created_at
    return oldest_date

def extract_ten_year_data(data, start_date, end_date):
    extract_data = []
    for item in data:
        created_at = datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S")
        if start_date <= created_at <= end_date:
            extracted_item = {
                "author": item.get("author", ""),
                "condition": item.get("condition", []),
                "consequent": item.get("consequent", []),
                "created_at": item.get("created_at", "")
            }
            extract_data.append(extracted_item)
    return extract_data

if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.RESOURCE}/{owner}"
    out_path = f"{path.RESOURCE}/ten_year_{owner}"
    projects = list_files_in_directory(dir_path)

    for project in tqdm(projects, leave=False):
        data = load_from_json(f"{dir_path}/{project}")
        project_start_date = get_oldest_date(data)
        if project_start_date is not None:  # Check if the start date was found
            project_end_date = project_start_date + timedelta(days=10*365)
            extracted_data = extract_ten_year_data(data, project_start_date, project_end_date)
            dump_to_json(extracted_data, f"{out_path}/{project}")
