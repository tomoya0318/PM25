import json
from tqdm import tqdm
from constants import path
from utils.file_processor import decode_unicode_escapes, dump_to_json, list_files_in_directory


def extract_author(file_path):
    """JSONファイルから，パッチ作成者とそのコミット回数を取得する

    Args:
        file_path (str): データを含むJSONファイルへのパス

    Returns:
        dict: パッチ作成者とそのコミット回数
    """
    with open(file_path, "r") as file:
        data = json.load(file)

    result = {}
    for item in tqdm(data, leave=False):
        author = decode_unicode_escapes(item["author"])
        if author in result:
            result[author] += 1
        else:
            result[author] = 1
    return result


def save_author_to_json(authors, save_path):
    """開発者の情報をJSONファイルに保存

    Args:
        authors (dict): 保存する開発者の情報を含む辞書
        save_path (str): 保存するファイルのパス
    """
    dump_to_json(authors, save_path)


if __name__ == "__main__":
    """データに存在する開発者と，その人のコミット数をjsonファイルとして出力
    """
    owner = "numpy"
    dir_path = f"{path.INTERMEDIATE}/train_data/{owner}"
    projects = list_files_in_directory(dir_path)
    for project in tqdm(projects, leave=False):
        file_path = f"{dir_path}/{project}"
        output_path = f"{path.INTERMEDIATE}/dev/{owner}/{project}"
        authors = extract_author(file_path)
        save_author_to_json(authors, output_path)
