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
                diff.append(f"={token}")

    return diff


def merge_consecutive_tokens(diff):
    """連続するトークンを結合する．

    Args:
        diff (list): トークンのリスト

    Returns:
        list: 結合されたトークンのリスト
    """
    if not diff:
        return []

    merged_diff = []
    current_token = diff[0]

    for token in diff[1:]:
        if current_token.startswith(('-', '+', '=')) and token.startswith(current_token[0]):
            current_token += token[1:]
            continue
        merged_diff.append(current_token[1:] if current_token.startswith("=") else current_token)
        current_token = token

    merged_diff.append(current_token)
    return merged_diff

# debag
if __name__ == "__main__":
    condition = "i=dic[STRING]"
    consequent = "i=dic.get(STRING)"
    token = compute_token_diff(condition, consequent)
    print(token)
    print(merge_consecutive_tokens(token))