import sys
from pathlib import Path

# プロジェクトのルートディレクトリを追加
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / "src"))
