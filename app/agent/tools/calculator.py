import ast
import operator as op
from typing import cast

_BIN = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}
_UNARY = {ast.USub: op.neg, ast.UAdd: op.pos}


def safe_eval(expression: str) -> float:
    if len(expression) > 200:
        raise ValueError("Занадто довгий вираз")

    def ev(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return cast(float | int, node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            return _BIN[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](ev(node.operand))
        raise ValueError("Недозволений вираз")

    return ev(ast.parse(expression, mode="eval"))