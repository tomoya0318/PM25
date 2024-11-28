"""使用するPATHの一覧
"""

import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA = os.path.join(ROOT, "data")
RESOURCE = os.path.join(DATA, "resources")
INTERMEDIATE = os.path.join(DATA, "out", "intermediate")
RESULTS = os.path.join(DATA, "out", "results")
TMP = os.path.join(ROOT, "tmp")
