import os
import shutil
import json


def get_filename(file_path):
    """
    指定されたファイル名から拡張子を除いた部分を取得

    Args:
        filename (str): ファイル名

    Returns:
        str: 拡張子を除いたファイル名
    """
    filename_with_extension = os.path.basename(file_path)
    filename_without_extension = os.path.splitext(filename_with_extension)[0]
    return filename_without_extension


def ensure_dir_exists(file_path):
    """
    指定されたファイルパスのディレクトリが存在するか確認し、存在しない場合は作成

    Args:
        filepath (str): 確認および作成するディレクトリを含むファイルパス
    """
    dir = os.path.dirname(file_path)
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
        print(f"Directory created: {dir}")
    else:
        print(f"Directory already exists: {dir}")


def decode_unicode_escapes(s):
    """
    エスケープされたユニコード文字列をデコードする。

    Args:
        s (str): エスケープされたユニコード文字列

    Returns:
        str: デコードされた文字列
    """
    # まず最初にエスケープシーケンスをデコード
    decoded_bytes = bytes(s, "utf-8").decode("unicode_escape")
    # 次にUTF-8として解釈しなおす
    return decoded_bytes.encode("latin1").decode("utf-8")


def remove_dir(dir_path):
    """指定したディレクトリを削除

    Args:
        dir_path (str): 削除したいディレクトリへのパス
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


def load_from_json(file_path):
    """JSONファイルからデータを取得

    Args:
        file_path (str): JSONファイルへのパス
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    return data


def dump_to_json(data, file_path):
    """
    データをJSONファイルへ保存する関数。

    Args:
        data (any): 保存するデータ
        file_path (str): JSONファイルへのパス
    """
    ensure_dir_exists(file_path)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def format_pattern(pattern):
    """
    パターン文字列をフォーマットしてリストに変換する関数

    Args:
        pattern (str): フォーマットするパターン文字列．例: "(a, b, c)"

    Returns:
        list: フォーマットされたパターンのリスト．例: ['a', 'b', 'c']
    """
    return pattern.strip("()").split(", ")


def list_files_in_directory(directory):
    """指定されたディレクトリ内のすべてのファイル名を取得する関数

    Args:
        directory (str): 対象のディレクトリのパス

    Returns:
        list: ファイル名のリスト
    """
    try:
        file_names = os.listdir(directory)
        return file_names
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []