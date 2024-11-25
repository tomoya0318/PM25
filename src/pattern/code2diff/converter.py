import difflib
import tokenize
from tqdm import tqdm
from codetokenizer.tokenizer import TokeNizer
from pattern.code2diff.source_preprocessor import variable_name_preprocessing, extract_diff
from utils.file_processor import dump_to_json
from constants import path


def compute_token_diff(condition: str, consequent: str, language: str) -> list[str] | dict[str, str]:
    """トークン化された2つのコード文字列の差分を計算する．

    Args:
        condition (str): 変更前のコード文字列
        consequent (str): 変更後のコード文字列

    Returns:
        list: 差分を示すトークンのリスト．削除されたトークンには「-」、追加されたトークンには「+」が付く．
    """
    TN = TokeNizer(language)
    try:
        token_condition = TN.getPureTokens(variable_name_preprocessing(condition))
        token_consequent = TN.getPureTokens(variable_name_preprocessing(consequent))
    except tokenize.TokenError as e:
        return {"error": str(e)}

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

    for token in tqdm(diff[1:], desc="merging token", leave=False):
        if current_token.startswith(("-", "+", "=")) and token.startswith(current_token[0]):
            current_token += token[1:]
            continue
        merged_diff.append(current_token)
        current_token = token

    merged_diff.append(current_token)
    return merged_diff


def main():
    project = f"{path.INTERMEDIATE}/sample/vscode#87709.json"
    out_path = f"{path.RESULTS}/sample/vscode#87709.json"
    patch_data = extract_diff(project)
    result = []
    for language, condition, consequent in patch_data:
        diff = compute_token_diff(condition, consequent, language)
        if isinstance(diff, dict) and "error" in diff:
            print(f"エラーが発生しました: {diff["error"]}")
            continue
        if isinstance(diff, list) and not diff:
            continue
        merged_diff = merge_consecutive_tokens(diff)
        result.append(merged_diff)
    dump_to_json(result, out_path)


if __name__ == "__main__":
    main()
