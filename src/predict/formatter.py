from constants import path
from utils.file_processor import load_from_json, dump_to_json, get_filename, list_files_in_directory


def split_data(file_path, dir_name):
    """学習用とテスト用にデータを分割（8:2）

    Args:
        file_path (str): 元のデータへのpath
    """
    file_name = get_filename(file_path)
    data = load_from_json(file_path)
    data = _extract_required_data(data)
    # データを前半2割をテストデータとして、後半8割を学習データとして分割
    split_index = int(len(data) * 0.2)
    test_data = data[:split_index]
    train_data = data[split_index:]
    dump_to_json(train_data, f"{path.INTERMEDIATE}/train_data/{dir_name}/{file_name}.json")
    dump_to_json(test_data, f"{path.INTERMEDIATE}/test_data/{dir_name}/{file_name}.json")


def _extract_required_data(data):
    """
    入力データから condition, consequent, author の情報だけを抜き出す関数。

    Args:
        data (list): 入力データのリスト

    Returns:
        list: 抜き出した情報を含む辞書のリスト
    """
    extracted_data = []
    for item in data:
        extracted_item = {
            "author": item.get("author", ""),
            "condition": item.get("condition", []),
            "consequent": item.get("consequent", []),
        }
        extracted_data.append(extracted_item)
    return extracted_data


if __name__ == "__main__":
    owner = "numpy"
    dir_path = f"{path.RESOURCE}/{owner}"
    projects = list_files_in_directory(dir_path)
    for project in projects:
        file_path = f"{dir_path}/{project}"
        split_data(file_path, owner)
