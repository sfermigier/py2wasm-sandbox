"""
Step 1:

- 01: i32 literal
"""
import ast
from _ast import AST
from pathlib import Path

from devtools import debug


def LF():
    return "\n"


def TAB():
    return "  "


def compile(source: str):
    root = ast.parse(source)
    wat = compile_tree(root)
    debug(wat)
    Path("generated.wat").write_text(wat)


def compile_tree(tree):
    main_block = generate(tree)

    block = "(module" + LF()
    block += TAB() + '(export "exported_main" (func $main))' + LF()
    block += TAB() + "(func $main (result i32)" + LF()
    block += TAB() + TAB() + main_block + LF()
    block += TAB() + TAB() + "return" + LF()
    block += TAB() + ")" + LF()
    block += ")"

    return block


def generate(tree: AST | list[AST]):
    match tree:
        case ast.Module(body):
            return generate(body)

        case [*nodes]:
            return "\n".join(generate(node) for node in nodes)

        case ast.Expr(value):
            return generate(value)

        case ast.Constant(value):
            return generate(value)

        case int(n):
            # block = 'i32.const ' + str(v)
            return f"i32.const {n}"

        case _:
            raise NotImplementedError(f"Unknown node {tree!r}")
