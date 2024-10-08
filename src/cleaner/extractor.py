from datetime import datetime, timedelta
from tqdm import tqdm
from utils.file_processor import load_from_json, list_files_in_directory, dump_to_json
from constants import path

def get_oldest_date(data):
    oldest_date = None
    for item in data:
        created_at = datetime.strptime(item["created_at"].split()[0], "%Y-%m-%d")
        if oldest_date is None or created_at < oldest_date:
            oldest_date = created_at
    return oldest_date

def extract_term_data(data, start_date, end_date):
    extract_data = []
    for item in data:
        created_at = datetime.strptime((item["created_at"]).split()[0], "%Y-%m-%d")
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
    out_path = f"{path.RESOURCE}/2020to2024_{owner}"
    START_DATE = datetime.strptime("2020-1-1", "%Y-%m-%d")
    END_DATE = datetime.strptime("2024-1-1", "%Y-%m-%d")
    projects = list_files_in_directory(dir_path)
    cnt = 0

    for project in tqdm(projects, leave=False):
        data = load_from_json(f"{dir_path}/{project}")
        project_start_date = get_oldest_date(data)
        if project_start_date != None and project_start_date < START_DATE:
            extracted_data = extract_term_data(data, START_DATE, END_DATE)
            if not extracted_data:
                continue
            cnt += 1
            dump_to_json(extracted_data, f"{out_path}/{project}")

    print(cnt)