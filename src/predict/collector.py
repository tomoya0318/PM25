from utils.ast_checker import are_ast_equal
from utils.file_processor import format_pattern


def collect_triggerable_patches(pattern):
    """トリガーシーケンスを特定

    Args:
        patterns (dict): パターンの辞書

    Returns:
        str: トリガーシーケンス
    """
    trigger = ""
    pattern = format_pattern(pattern)
    for token in pattern:
        token = token.strip("'")
        if token.startswith("-") or token.startswith("="):
            trigger += token[1:]
    return trigger


def apply_change(pattern):
    """
    パターンを適用後のコードを特定する関数。

    Args:
        pattern (str): 適用するパターン．例: "('+token1', '=token2', '-token3')"

    Returns:
        str: 適用後のコード．例: "token1token2"
    """
    destination = ""
    pattern = format_pattern(pattern)
    for token in pattern:
        token = token.strip("'")
        if token.startswith("+") or token.startswith("="):
            destination += token[1:]
    return destination


def apply_pattern_changes(patterns, conditon):
    """パターンの変更を適用する関数

    Args:
        patterns (dict): パターンの辞書
        condition (str): 変更前のコード

    Returns:
        str: 適用後の結果
    """
    for pattern in patterns:
        # キーの文字列をトークンに分割
        trigger = collect_triggerable_patches(pattern)
        if not are_ast_equal(trigger, conditon):
            continue
        pre_consequent = apply_change(pattern)
        return pre_consequent

    return None


if __name__ == "__main__":
    pattern = {
        "('=i=dic', '-[', '+.get(', '=STRING', '-]', '+)')": 2,
        "('=i=dic', '-[', '+.get(', '=Nuv', '-]', '+)')": 2,
    }
    print(apply_pattern_changes(pattern, "i=dic[STRING]"))
