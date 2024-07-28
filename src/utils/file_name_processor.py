import os

def get_filename(filename):
    """
    指定されたファイル名から拡張子を除いた部分を取得します。

    Args:
        filename (str): ファイル名

    Returns:
        str: 拡張子を除いたファイル名
    """
    return os.path.splitext(filename)[0]
