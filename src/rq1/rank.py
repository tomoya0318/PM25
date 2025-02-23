from pathlib import Path

from constants import path
from rq1.cut import iter_json_items


def main(input_path: Path, pattern: list[str]):
    rank = 1
    skip_count = 0
    pre_support = None

    for item in iter_json_items(input_path):
        # ランク計算処理
        if pre_support is None or pre_support != item.support:
            rank += skip_count
            skip_count = 1
        else:
            skip_count += 1

        pre_support = item.support

        # パターンが一致した場合の表示
        if item.pattern == pattern:
            print(f"{rank}位 (support={item.support})")
            break
    else:
        print("パターンが見つかりませんでした。")


if __name__ == "__main__":
    full_pattern_path = path.RESULTS / "openstack_s10_t15" / "all" / "merged_all_nova_2013to2025.json"
    pattern = ["-str", "-(", "-uuid", "+uuidutils", "=.", "-uuid4", "+generate_uuid", "=(", "=)", "-)"]

    main(full_pattern_path, pattern)
