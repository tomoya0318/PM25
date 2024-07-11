import sys
sys.path.append("./")
from source_preprocessor import variable_name_preprocessing, tokenize_python_code

def compute_token_diff(condition, consequent):
    token_condition = tokenize_python_code(variable_name_preprocessing(condition))
    token_consequent = tokenize_python_code(variable_name_preprocessing(consequent))

if __name__ == "__main__":
    compute_token_diff()