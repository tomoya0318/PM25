from pathlib import Path

from pattern.diff2sequence import extract_diff

def calc_confidence(pattern: list[str], diff_path: Path) -> float:
    triggerable_count = 0
    actually_changed_count = 0

    for _, _, diff_hunk in extract_diff(diff_path):
        if _is_trigger_sequence(pattern, diff_hunk.condition):
            triggerable_count += 1
            if _is_actually_chnage(pattern, diff_hunk.consequent):
                actually_changed_count += 1

    if triggerable_count == 0:
        return 0.0

    return round(actually_changed_count / triggerable_count, 2)

def _is_trigger_sequence(pattern: list[str], condition: list[str]) -> bool:
    """パターンが適用可能か判定"""
    trigger = [token.lstrip("-=") for token in pattern if token.startswith("-") or token.startswith("=")]
    if not trigger:
        return False

    before_code = "".join(condition)

    for t in trigger:
        if t not in before_code:
            return False

    return True


def _is_actually_chnage(pattern: list[str], consequent: list[str]) -> bool:
    """パターンによる変更があるか判定"""
    actually_change = [token.lstrip("+=") for token in pattern if token.startswith("+") or token.startswith("=")]
    if not actually_change:
        return False

    after_code = "".join(consequent)
    for change in actually_change:
        if change not in after_code:
            return False

    return True