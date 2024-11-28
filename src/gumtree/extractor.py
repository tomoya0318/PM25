from models.diff import DiffHunk
from models.gumtree import Action, UpdateChange


def extract_update_code_changes(condition: list, consequent: list, actions: list[Action]) -> list[UpdateChange]:
    """update-nodeのアクションに対応する行全体を変更前後のコードから抽出する

    Args:
        condition (str): 変更前のコード全体
        consequent (str): 変更後のコード全体
        actions (list[dict]): GumTreeのアクション情報

    Returns:
        list[dict]: 変更情報のリスト。各要素は以下の形式：
            {
                "before": str,  # 変更前のコード行
                "after": str,   # 変更後のコード行
            }
    """
    update_changes = []

    # 各行の開始位置を計算
    condition_positions = []
    pos = 0
    for line in condition:
        condition_positions.append(pos)
        pos += len(line) + 1  # +1 は改行文字の分

    for action in actions:
        if action.action == "update-node":
            # ツリー情報から位置情報を抽出
            tree_info = action.tree
            pos_str = tree_info[tree_info.rfind("[") + 1:tree_info.rfind("]")]
            start, _ = map(int, pos_str.split(","))

            # 該当する行を見つける
            for i, line_start in enumerate(condition_positions):
                next_line_start = condition_positions[i + 1] if i + 1 < len(condition_positions) else len(''.join(condition))
                if line_start <= start < next_line_start:
                    before_line = condition[i]
                    after_line = consequent[i]
                    update_changes.append(UpdateChange(
                        before=before_line,
                        after=after_line
                    ))
                    break

    return update_changes

# 使用例
if __name__ == "__main__":
    condition = [
        "ASSERT_EQ(expected, actual);",
        "ASSERT_EQ(expected2, actual2);",
        "ASSERT_EQ(expected3, actual3);"
    ]

    consequent = [
        "EXPECT_EQ(expected, actual);",
        "EXPECT_EQ(expected2, actual2);",
        "EXPECT_EQ(expected3, actual3);"
    ]

    actions = [
        Action(
        action="update-node",
        tree="identifier: ASSERT_EQ [0,9]",
        label="EXPECT_EQ"
        ),
        Action(
        action="update-node",
        tree="identifier: ASSERT_EQ [61,70]",
        label="EXPECT_EQ"
        )
    ]
    changes = extract_update_code_changes(condition, consequent, actions)
    for change in changes:
        print(f"Before: {change.before}")
        print(f"After:  {change.after}\n")