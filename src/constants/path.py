"""使用するPATHの一覧
"""
from pathlib import Path


ROOT = Path(__file__).parents[2]
DATA = ROOT / "data"
RESOURCE = DATA / "resources"
INTERMEDIATE = DATA / "out" / "intermediate"
RESULTS = DATA / "out" / "results"
TMP = ROOT / "tmp"