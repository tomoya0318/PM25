import re
import tokenize
import json
from io import BytesIO
from tqdm import tqdm
import os


def variable_name_preprocessing(code):
    """
    変数名のプレースホルダー形式を正規の名前形式に変換します．

    入力されたコード内の ${数字:NAME} 形式のプレースホルダーを
    そのまま NAME の形式に変換します．

    Args:
        code (str): 変換対象のコード文字列．

    Returns:
        str: プレースホルダーが変換されたコード文字列
    """
    pattern = re.compile(r"\$\{\d+:([A-Z]+)\}")

    def replace_token(match):
        return match.group(1)

    # 変換処理
    converted_code = pattern.sub(replace_token, code)
    return converted_code


def tokenize_python_code(code):
    """与えられたPythonコードをトークン化し，改行文字や空のトークンを除いたトークンのリストを返す．

    Args:
        code (str): トークン化対象のPythonコード文字列．

    Returns:
        list: トークンのリスト．各トークンはコード内の文字列を表す．
    """
    tokens = []
    readline = BytesIO(code.encode("utf-8")).readline
    for tok in tokenize.tokenize(readline):
        if tok.type not in [tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT]:
            token_value = tok.string.strip()
            if token_value:  # 空でないトークンを追加
                tokens.append(token_value)
    return tokens


def extract_diff(file_path):
    """JSONファイルから，変更前と変更後のペアを抽出する

    Args:
        file_path (str): データを含むJSONファイルへのパス

    Returns:
        list: 各サブリストが[変更前, 変更後]のペアとなるリスト
    """
    with open(file_path, "r") as file:
        data = json.load(file)

    result = []
    print("extract diff start...")
    for item in tqdm(data):
        condition = item["condition"]
        consequent = item["consequent"]
        try:
            result.append([condition[0], consequent[0]])
        except IndexError:
            continue
    return result


def save_patterns_to_json(filtered_patterns, filepath):
    """フィルタリングされたパターンをJSONファイルに保存する

    Args:
        filtered_patterns (dict): パターンとその出現回数の辞書
        filepath (str): 保存するJSONファイルのパス
    """
    # JSONシリアライズに適した辞書に変換
    patterns_dict = {str(subseq): count for subseq, count in filtered_patterns.items()}
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # 辞書をJSONファイルに保存
    with open(filepath, 'w') as f:
        json.dump(patterns_dict, f, indent=4)