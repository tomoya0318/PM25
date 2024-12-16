import ast
import astor


class DocstringAndCommentRemover(ast.NodeTransformer):
    def visit_Module(self, node):
        if ast.get_docstring(node):
            node.body = node.body[1:]
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if ast.get_docstring(node):
            node.body = node.body[1:]
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        if ast.get_docstring(node):
            node.body = node.body[1:]
        return self.generic_visit(node)


def remove_docstring(source_code: str) -> str:
    """
    Pythonコードからdocstringを削除する
    """
    try:
        # コードをASTに変換
        tree = ast.parse(source_code)

        # DocstringAndCommentRemoverを適用
        transformer = DocstringAndCommentRemover()
        modified_tree = transformer.visit(tree)

        # 修正されたASTをコードに戻す
        return astor.to_source(modified_tree)
    except SyntaxError:
        # 構文エラーが発生した場合は元のコードを返す
        return source_code


def remove_comments(source_code: str) -> str:
    """
    Pythonコードからコメントを削除する
    """
    lines = source_code.splitlines()
    result = []
    for line in lines:
        if line.strip().startswith("#"):
            continue
        else:
            result.append(line)
    return "\n".join(result)
