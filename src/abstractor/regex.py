import re


def is_abstracted_pattern(pattern: list[str]) -> bool:
    for token in pattern:
        if any(keyword in token for keyword in ("VAR", "STRING", "NUMBER")):
            return True
    return False


def split_pattern(pattern: list[str]):
    """変更前パターンと変更後パターンに分割

    Args:
        pattern (list[str]): 元のパターン

    Returns:
        tuple: (変更前パターン，変更後パターン)
    """
    trigger = [token[1:] for token in pattern if token.startswith("-") or token.startswith("=")]
    actually_change = [token[1:] for token in pattern if token.startswith("+") or token.startswith("=")]

    return trigger, actually_change


def pattern_to_regex(pattern: list[str])-> re.Pattern[str]:
    regex = ""
    for token in pattern:
        if "VAR" in token or "FUNCTION" in token:
            regex += r"[a-zA-Z_][a-zA-Z0-9_]*"
        elif "STRING" in token:
            regex += r"['\"]([^'\"]*)['\"]"
        elif "NUMBER" in token:
            regex += r"\b\d+\b"
        else:
            regex += re.escape(token)
    return re.compile(regex)


if __name__ == "__main__":
    pattern = [
        "=VAR_1",
        "==",
        "-{",
        "-}",
        "+objects",
        "+.",
        "+ImageMeta",
        "+.",
        "+from_dict",
        "+(",
        "+self",
        "+.",
        "+test_VAR_1",
        "+)",
    ]
    # pattern = ["==", "-:", "+,"]
    pre, after = split_pattern(pattern)
    pre_pattern = pattern_to_regex(pre)
    post_pattern = pattern_to_regex(after)
    # text = "image_meta={}"
    text = "image_meta=objects.ImageMeta.from_dict(self.test_image_meta)"

    if post_pattern.search(text):
        print("post")
    elif pre_pattern.search(text):
        print("pre")
