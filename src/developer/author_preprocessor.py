import json
from tqdm import tqdm
from utils.file_processor import ensure_dir_exists, decode_unicode_escapes, load_from_json


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
        author = decode_unicode_escapes(item["author"])
        try:
            result.add(author)
        except IndexError:
            continue
    return result


def save_author_to_json(authors, save_path):
    """開発者の情報をJSONファイルに保存

    Args:
        authors (set): 保存する開発者の情報を含む集合
        file_name (str): 保存するファイルの名前
    """
    ensure_dir_exists(save_path)
    authors_list = list(authors)  # setをリストに変換
    with open(save_path, "w") as f:
        json.dump(authors_list, f, indent=4, ensure_ascii=False)


def json_to_set(save_path):
    """jsonで保存されているデータを集合に変換

    Args:
        save_path (str): 保存されているデータへのパス

    Returns:
    set: JSONファイル内のデータをセットに変換したもの
    """
    authors = set(load_from_json(save_path))
    return authors
