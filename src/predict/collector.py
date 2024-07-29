def collect_triggerable_patches(pattern):
    """トリガー可能なパッチを収集する

    Args:
        pattern (dict): パターンの辞書

    Returns:
        list: トリガー可能なトークンのリスト
    """
    triggers = set()
    for key in pattern:
        # キーの文字列をトークンに分割
        tokens = key.strip("()").split(", ")
        trigger = []
        for token in tokens:
            token = token.strip("'")
            if token.startswith('-') or token.startswith('='):
                trigger.append(token)
        triggers.add(tuple(trigger))
    return triggers
