from utils.file_processor import format_pattern, load_from_json
from constants import path


def calc_pattern_match_rate(pattern1, pattern2):
    intersection = pattern1 & pattern2
    union = pattern1 | pattern2

    if len(union) == 0:
        return 0.0

    return len(intersection) / len(union)


def format_all_pattern(patterns):
    result = set()
    for pattern in patterns:
        pattern = format_pattern(pattern)
        result.add(tuple(pattern))
    return result


if __name__ == "__main__":
    pattern1 = load_from_json(f"{path.INTERMEDIATE}/pattern/numpy_numpy_Python_master_pattern_train.json")
    pattern2 = load_from_json(f"{path.INTERMEDIATE}/pattern/numpy_numpy_Python_master_pattern_test.json")
    pattern1 = format_all_pattern(pattern1)
    pattern2 = format_all_pattern(pattern2)
    print(calc_pattern_match_rate(pattern1, pattern2))
