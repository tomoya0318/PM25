import itertools
from collections import defaultdict
from pathlib import Path

from joblib import Parallel, delayed

from constants import path
from exception import JSONProcessingError
from models.pattern import PatternWithSupport
from utils.file_processor import stream_json_patterns


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
        items = stream_json_patterns(file_path)
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
    input_path = path.RESULTS / "openstack" / "all" / "merged_15_nova_support10.json"
    print("処理開始...")
    try:
        result = parallel_count_token_length(
            input_path, chunk_size=2000, n_jobs=-1  # メモリ使用量と処理速度のバランスを調整
        )
        print("\n処理結果:")
        for length in sorted(result):
            print(f"長さ {length}: {result[length]}件")
    except Exception as e:
        print(f"致命的なエラーが発生しました: {str(e)}")
