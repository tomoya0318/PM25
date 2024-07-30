from sklearn.model_selection import train_test_split
from constants import path
from utils.file_processor import load_from_json, dump_to_json, get_filename

def split_data(file_path):
    """学習用とテスト用にデータを分割（8:2）

    Args:
        file_path (str): 元のデータへのpath
    """
    file_name = get_filename(file_path)
    data = load_from_json(file_path)
    data = _extract_required_data(data)
    # データを学習用データとテスト用データに分割
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
    dump_to_json(train_data, f"{path.INTERMEDIATE}/train_data/{file_name}.json")
    dump_to_json(test_data, f"{path.INTERMEDIATE}/test_data/{file_name}.json")

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
            "consequent": item.get("consequent", [])
        }
        extracted_data.append(extracted_item)
    return extracted_data

if __name__ == "__main__":
    file_path = f"{path.RESOURCE}/sample_data.json"
    split_data(file_path)