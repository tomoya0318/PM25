import builtins
import json
import keyword
from pathlib import Path


class IdentifierDict:
    def __init__(self, additional_dict_path: Path | None = None):
        self.method_names = set()
        self._load_builtin_methods()
        self._load_common_methods()
        if additional_dict_path:
            self._load_additional_methods(additional_dict_path)

    def _load_builtin_methods(self):
        self.method_names.update(dir(builtins))
        self.method_names.update(keyword.kwlist)

    def _load_common_methods(self):
        # 基本的なメソッド名セット
        basic_methods = {
            # オブジェクト関連
            "__init__",
            "__str__",
            "__repr__",
            # データ構造操作
            "append",
            "extend",
            "pop",
            "clear",
            "update",
            # リソース管理
            "dispose",
            "cancel",
            "close",
            # その他一般的なメソッド
            "get",
            "set",
            "validate",
            "check",
        }
        self.method_names.update(basic_methods)

    def _load_additional_methods(self, dict_path: Path):
        """追加のメソッド名を読み込む"""
        try:
            with open(dict_path, "r") as f:
                additional_methods = set(json.load(f))
                self.method_names.update(additional_methods)
        except FileNotFoundError:
            print(f"Warning: Additional dictionary file not found at {dict_path}")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON format in {dict_path}")

    def should_preserve(self, identifier: str) -> bool:
        return identifier in self.method_names

    def add_method(self, method_name: str):
        """個別のメソッド名を追加"""
        self.method_names.add(method_name)

    def add_methods(self, method_names: set[str]):
        """複数のメソッド名を一度に追加"""
        self.method_names.update(method_names)
