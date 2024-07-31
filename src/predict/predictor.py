from utils.file_processor import load_from_json
from predict.collector import apply_pattern_changes
from utils.ast_checker import are_ast_equal
from constants import path


def apply_and_validate_patterns(pattern_path, test_path):
    """パターンを適用し、適合率と再現率を計算する関数

    Args:
        pattern_path (str): パターンが保存されたJSONファイルへのパス
        test_path (str): テストデータが保存されたJSONファイルへのパス

    Returns:
        tuple: 適合率と再現率
    """
    patterns = load_from_json(pattern_path)
    test_data = load_from_json(test_path)

    # テストデータにパターンを適用し，適合率，再現率を計算
    tp = 0
    fp = 0
    fn = 0

    for item in test_data:
        condition = item.get("condition", [])
        consequent = item.get("consequent", [])
        try:
            condition = condition[0]
            consequent = consequent[0]
        except IndexError:
            pass
        pre_consequent = apply_pattern_changes(patterns, condition)
        if pre_consequent:
            if are_ast_equal(pre_consequent, consequent):
                tp += 1
            else:
                fp += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    print(tp, fp, fn)
    return precision, recall


if __name__ == "__main__":
    pattern_path = f"{path.INTERMEDIATE}/pattern/numpy_numpy_Python_master_pattern.json"
    test_path = f"{path.INTERMEDIATE}/test_data/numpy_numpy_Python_master.json"

    precision, recall = apply_and_validate_patterns(pattern_path, test_path)

    print(precision, recall)
