from dataclasses import dataclass

from dataclasses_json import dataclass_json, DataClassJsonMixin
from joblib import Parallel, delayed
from pathlib import Path

from models.diff import DiffHunk
from pattern.parallel_diff import parallel_extract_diff
from utils.diff_handler import DiffDataHandler
from utils.file_processor import load_from_json


@dataclass_json
@dataclass
class ConfidenceResult(DataClassJsonMixin):
    pattern: list[str]
    confidence: float


def parallel_calc_confidence(pattern_path: Path, diff_path: Path) -> list[ConfidenceResult]:
    pattern_data_list = load_from_json(pattern_path)
    patterns: list[list[str]] = [data["pattern"] for data in pattern_data_list]

    data_list = DiffDataHandler.load_from_json(diff_path)
    diff_data = parallel_extract_diff(data_list)
    diff_hunks: list[DiffHunk] = [diff[1] for diff in diff_data]

    result = Parallel(n_jobs=-1, verbose=10)(
        delayed(calc_confidence)(pattern, diff_hunks) for pattern in patterns
    )

    return result # type: ignore


def calc_confidence(pattern: list[str], diff_hunks: list[DiffHunk]) -> ConfidenceResult:
    triggerable_count = 0
    actually_changed_count = 0

    for diff_hunk in diff_hunks:
        if is_trigger_sequence(pattern, diff_hunk.condition):
            triggerable_count += 1
            if is_actually_change(pattern, diff_hunk.consequent):
                actually_changed_count += 1

    if triggerable_count == 0:
        return ConfidenceResult(pattern, 0.0)

    return ConfidenceResult(pattern, round(actually_changed_count / triggerable_count, 2))


def is_trigger_sequence(pattern: list[str], condition: list[str] | str) -> bool:
    """パターンが適用可能か判定"""
    trigger = [token.lstrip("-=") for token in pattern if token.startswith("-") or token.startswith("=")]
    if not trigger:
        return False

    before_code = "".join(condition)

    for t in trigger:
        if t not in before_code:
            return False

    return True


def is_actually_change(pattern: list[str], consequent: list[str] | str) -> bool:
    """パターンによる変更があるか判定"""
    actually_change = [token.lstrip("+=") for token in pattern if token.startswith("+") or token.startswith("=")]
    if not actually_change:
        return False

    after_code = "".join(consequent)
    for change in actually_change:
        if change not in after_code:
            return False

    return True