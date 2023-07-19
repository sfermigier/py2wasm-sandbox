# mininode_wasm.py - Mini Node.js WASM translator by Node.js
# - 01: i32 literal
# - 02: binary operator
#   - 02: +
#   - 02: -, *, /, %
import ast
from _ast import AST
from pathlib import Path

from devtools import debug


def LF():
    return "\n"


def TAB():
    return "  "


def TABs(n):
    return TAB() * n


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
    block += main_block + LF()
    block += TAB() + TAB() + "return" + LF()
    block += TAB() + ")" + LF()
    block += ")"

    return block


def generate(tree: AST | list[AST], indent=0):
    match tree:
        case ast.Module(body):
            return generate(body)

        case [*nodes]:
            return "\n".join(generate(node) for node in nodes)

        case ast.Expr(value):
            return generate(value)

        case ast.Constant(value):
            return TABs(indent) + generate(value)

        case ast.BinOp(left, op, right):
            left_block = generate(left, 2)
            right_block = generate(right, 2)
            match op:
                case ast.Add():
                    wasm_op = "i32.add"
                case ast.Sub():
                    wasm_op = "i32.sub"
                case ast.Mult():
                    wasm_op = "i32.mul"
                case ast.Div():
                    wasm_op = "i32.div_s"
                case ast.Mod():
                    wasm_op = "i32.rem_s"
                case _:
                    raise NotImplementedError(f"Unknown operator {op!r}")
            return left_block + LF() + right_block + LF() + TABs(2) + wasm_op

        case int(n):
            return f"i32.const {n}"

        case _:
            raise NotImplementedError(f"Unknown node {tree!r}")
