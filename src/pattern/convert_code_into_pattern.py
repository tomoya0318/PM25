import re
import tokenize
from io import BytesIO

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
    pattern = re.compile(r'\$\{\d+:([A-Z]+)\}')

    def replace_token(match):
        return match.group(1)
    
    # 変換処理
    converted_code = pattern.sub(replace_token, code)
    return converted_code

def tokenize_python_code(code):
    """与えられたpythonコードをトークン化し，改行文字をのぞいたトークンのリストを返す．

    Args:
        code (str): トークン化対象のPythonコード文字列．

    Returns:
        list: トークンのリスト．各トークンはコード内の文字列を表す．
    """
    tokens = []
    readline = BytesIO(code.encode('utf-8')).readline
    for tok in tokenize.tokenize(readline):
        if tok.type not in [tokenize.ENCODING, tokenize.NL, tokenize.NEWLINE]:
            tokens.append(tok.string)
    return tokens