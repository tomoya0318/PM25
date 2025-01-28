import itertools
import mmap
from collections import defaultdict
from pathlib import Path
from typing import Generator

import ijson
from joblib import Parallel, delayed

from constants import path
from models.pattern import PatternWithSupport


class JSONProcessingError(Exception):
    """カスタム例外クラス"""

    pass


def stream_json_items(file_path: Path) -> Generator[dict, None, None]:
    """メモリマップを使用したJSONストリーミング処理"""
    try:
        with file_path.open("rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                mm.madvise(mmap.MADV_SEQUENTIAL)
                for item in ijson.items(mm, "item"):
                    yield item
    except Exception as e:
        raise JSONProcessingError(f"JSONストリーミングエラー: {str(e)}")


def process_chunk(chunk: list[dict]) -> dict[int, int]:
    """チャンク単位の処理"""
    chunk_counts = defaultdict(int)
    for item in chunk:
        try:
            pattern = PatternWithSupport.from_dict(item)
            length = len(pattern.pattern)
            chunk_counts[length] += 1
        except Exception as e:
            print(f"アイテム処理エラー: {str(e)}")
    return dict(chunk_counts)


def parallel_count_token_length(file_path: Path, chunk_size: int = 1000, n_jobs: int = -1) -> dict[int, int]:
    """並列処理によるトークン長カウント"""
    total_counts = defaultdict(int)

    try:
        items = stream_json_items(file_path)
        results = Parallel(n_jobs=n_jobs, verbose=10)(
            delayed(process_chunk)(list(itertools.islice(items, chunk_size)))
            for _ in iter(lambda: list(itertools.islice(items, chunk_size)), [])
        )

        for chunk_result in results:
            for length, count in chunk_result.items():  # type: ignore
                total_counts[length] += count

    except JSONProcessingError as e:
        print(f"処理中断: {str(e)}")
        raise

    return dict(total_counts)


if __name__ == "__main__":
    input_path = path.RESULTS / "openstack" / "all" / "merged_nova.json"

    print("処理開始...")
    try:
        result = parallel_count_token_length(
            input_path, chunk_size=2000, n_jobs=-1  # メモリ使用量と処理速度のバランス調整
        )
        print("\n処理結果:")
        with open("pattern_length_counts.txt", "w") as f:
            for length in sorted(result):
                f.write(f"長さ {length}: {result[length]}件\n")
                print(f"長さ {length}: {result[length]}件")
    except Exception as e:
        print(f"致命的なエラーが発生しました: {str(e)}")
