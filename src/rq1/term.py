import string

from models.pattern import PatternWithSupport


def is_long_pattern(pattern: list[str], length: int) -> bool:
    if len(pattern) <= length:
        return False
    return True


def is_all_symbols(pattern: list[str]) -> bool:
    return all(token[1:] in string.punctuation for token in pattern)


def is_subsequence(sub: list[str], seq: list[str]) -> bool:
    """`sub` が `seq` の順序を保った部分列であるかを確認"""
    it = iter(seq)
    return all(token in it for token in sub)


def is_change_pattern(pattern: list[str]):
    minus_flag = False
    pulas_flag = False

    for token in pattern:
        if token.startswith("-"):
            minus_flag = True
        if token.startswith("+"):
            pulas_flag = True

    return minus_flag and pulas_flag


def remove_subset_patterns(patterns: list[PatternWithSupport]) -> list[PatternWithSupport]:
    """順序を考慮して部分的に重複するパターンを削除"""
    # パターンを長さ順に降順ソート
    patterns.sort(key=lambda x: sum(len(token) for token in x.pattern), reverse=True)

    unique_patterns = []
    print("start remove")
    for pattern in patterns:
        if not any(is_subsequence(pattern.pattern, other.pattern) for other in unique_patterns):
            unique_patterns.append(PatternWithSupport(pattern.pattern, pattern.support))
    return unique_patterns
