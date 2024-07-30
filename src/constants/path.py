"""使用するPATHの一覧
"""

import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA = f"{ROOT}/data"
RESOURCE = f"{DATA}/resources"
INTERMEDIATE = f"{DATA}/out/intermediate"
RESULTS = f"{DATA}/out/results"
TMP = f"{ROOT}/tmp"
