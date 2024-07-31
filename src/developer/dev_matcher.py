def calc_dev_match_rate(dev1, dev2):
    """2つのプロジェクトの開発者の一致率を計算

    Args:
        dev1 (set): 1つ目の開発者の集合
        dev2 (set): 2つ目の開発者の集合

    Returns:
        float: 一致率
    """
    intersection = dev1 & dev2
    union = dev1 | dev2

    if len(union) == 0:
        return 0.0

    return len(intersection) / len(union)
