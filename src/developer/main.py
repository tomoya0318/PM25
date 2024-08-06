from developer.dev_commit_matcher import calc_dev_match_rate
from developer.author_preprocessor import json_to_set
from constants import path

if __name__ == "__main__":
    authors1_json = f"{path.INTERMEDIATE}/dev/"
    authors2_json = f"{path.INTERMEDIATE}/dev/"

    author1 = json_to_set(authors1_json)
    author2 = json_to_set(authors2_json)

    calc_dev_match_rate(author1, author2)
