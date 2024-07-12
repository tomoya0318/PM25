import difflib
import sys

sys.path.append("./src/pattern")
from source_preprocessor import variable_name_preprocessing, tokenize_python_code


def compute_token_diff(condition, consequent):
    """トークン化された2つのPythonコード文字列の差分を計算する．

    Args:
        condition (str): 変更前のPythonコード文字列
        consequent (str): 変更後のPythonコード文字列

    Returns:
       list: 差分を示すトークンのリスト．削除されたトークンには「-」、追加されたトークンには「+」が付く．
    """
    token_condition = tokenize_python_code(variable_name_preprocessing(condition))
    token_consequent = tokenize_python_code(variable_name_preprocessing(consequent))
    diff = []

    sm = difflib.SequenceMatcher(None, token_condition, token_consequent)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            for token in token_condition[i1:i2]:
                diff.append(f"-{token}")
            for token in token_consequent[j1:j2]:
                diff.append(f"+{token}")
        elif tag == "delete":
            for token in token_condition[i1:i2]:
                diff.append(f"-{token}")
        elif tag == "insert":
            for token in token_consequent[j1:j2]:
                diff.append(f"+{token}")
        elif tag == "equal":
            for token in token_condition[i1:i2]:
                diff.append(token)

    return diff

#debag
if __name__ == "__main__":
    print(compute_token_diff(
        "i=dic['STRING']",
        "i=dic.get('STRING')"
    ))
