import ast


def are_ast_equal(code1, code2):
    """
    2つのコード文字列が構文的に等しいかどうかを判定

    Args:
        code1 (str): 比較する最初のコード文字列
        code2 (str): 比較する2つ目のコード文字列

    Returns:
        bool: 2つのコード文字列が構文的に等しい場合はTrue、そうでない場合はFalseを返す
    """
    try:
        # エスケープ文字を考慮して文字列を処理
        if isinstance(code1, str):
            code1 = code1.encode("unicode_escape").decode("utf-8")
        if isinstance(code2, str):
            code2 = code2.encode("unicode_escape").decode("utf-8")

        # コード文字列をASTにパース
        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)

        # ASTを比較
        return ast.dump(tree1) == ast.dump(tree2)
    except SyntaxError:
        return False
