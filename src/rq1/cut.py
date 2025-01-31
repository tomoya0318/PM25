from itertools import islice

import ijson
import polars as pl
from typing import Generator
from constants import path


def iter_json_pattern(file_path):
    """
    JSONファイルから項目を逐次的に読み込むジェネレータ
    """
    with open(file_path, "r", encoding="utf-8") as f:
        # トップレベルの配列要素を逐次処理
        for item in ijson.items(f, "item"):
            result = ""
            for token in item["pattern"]:
                result += f"`{token}` "

            yield result


def iter_json_items(file_path) -> Generator[dict, None, None]:
    """
    JSONファイルから項目を逐次的に読み込むジェネレータ
    """
    with open(file_path, "r", encoding="utf-8") as f:
        # トップレベルの配列要素を逐次処理
        for item in ijson.items(f, "item"):
            yield {"pattern": item["pattern"], "support": item["support"]}


if __name__ == "__main__":
    base_path = path.RESULTS / "openstack" / "all"
    pre_path = base_path / "merged_15_nova_support10.json"
    pre_filter_path = base_path / "filtered_full_15_nova_support10.json"
    tmp_path = base_path / "filtered_15_nova_support10.json"
    output_path = base_path / "output.csv"
    pre_first_100_items = list(islice(iter_json_items(pre_path), 100))
    pre_filter_first_100_items = list(islice(iter_json_items(pre_filter_path), 100))
    tmp_first_100_items = list(islice(iter_json_items(tmp_path), 100))

    df = pl.DataFrame([pre_first_100_items, pre_filter_first_100_items, tmp_first_100_items])
    df.write_csv(output_path)
    print("end")
