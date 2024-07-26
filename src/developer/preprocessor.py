import json
import os
from tqdm import tqdm


def extract_author(file_path):
    """JSONファイルから，パッチ作成者を取得する

    Args:
        file_path (str): データを含むJSONファイルへのパス

    Returns:
        set: パッチ作成者（被りなし）
    """
    with open(file_path, "r") as file:
        data = json.load(file)

    result = set()
    print("extract developer start...")
    for item in tqdm(data):
        author = item["author"]
        try:
            result.add(author)
        except IndexError:
            continue
    return result


if __name__ == "__main__":
    json_file_path = os.path.join(os.path.dirname(__file__), "../../data/numpy_numpy_Python_master.json")
    print(extract_author(json_file_path))
