# mininode_wasm.py - Mini Node.js WASM translator by Node.js
# - 01: i32 literal
# - 02: binary operator
#   - 02: +
#   - 02: -, *, /, %
# - 03: multi-lines
# - 03: local variable
#   - 03: declare
#   - 03: initial value
#   - 03: refer
#   - 03: assign
# - 03: temp func
#   - 03: putn()

import ast
from ast import AST


def LF():
    return "\n"


def TAB():
    return "  "


def TABs(n):
    return TAB() * n


def compile(source: str) -> str:
    root = ast.parse(source)
    wat = compile_tree(root)
    return wat


def compile_tree(tree):
    lctx = {}
    main_block = generate(tree, 2, lctx)
    var_block = generate_variable_block(tree, 2, lctx)

    block = "(module" + LF()
    block += (
        TAB() + '(func $putn (import "imports" "imported_putn") (param i32))' + LF()
    )
    block += TAB() + '(export "exported_main" (func $main))' + LF()
    block += TAB() + "(func $main (result i32)" + LF()
    block += var_block + LF()
    block += main_block + LF()
    block += TAB() + TAB() + "return" + LF()
    block += TAB() + ")" + LF()
    block += ")"

    return block


def generate(tree: AST | list[AST], indent, lctx):
    match tree:
        case ast.Module(body):
            return generate(body, indent, lctx)

        case [*nodes]:
            return "\n".join(generate(node, indent, lctx) for node in nodes)

        case ast.Expr(value):
            return generate(value, indent, lctx)

        case ast.Constant(value):
            return TABs(indent) + generate(value, indent, lctx)

        case ast.BinOp(left, op, right):
            left_block = generate(left, 2, lctx)
            right_block = generate(right, 2, lctx)
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

        case ast.Call(func, args):
            match func:
                case ast.Name(id="putn"):
                    return generateCallPutn(args, indent, lctx)
                case _:
                    raise ValueError(f"Unknown function {func!r}")

        case ast.Assign(targets, value):
            assert len(targets) == 1
            target = targets[0]
            assert isinstance(target, ast.Name)
            name = target.id
            return assign_variable(name, value, indent, lctx)

        case ast.Name(id):
            return refer_variable(id, indent, lctx)

        case _:
            raise NotImplementedError(f"Unknown node {tree!r}")


def generateCallPutn(args, indent, lctx):
    """Debug function"""
    valueBlock = generate(args, indent, lctx)
    assert valueBlock

    block = valueBlock + LF()
    block += TABs(indent) + "call $putn" + LF()

    return block


# --- refer variable ---
def refer_variable(name, indent, lctx):
    # -- check EXIST --
    if name in lctx:
        var_name = lctx[name]
        block = TABs(indent) + "local.get " + var_name
        return block

    raise ValueError(f"Unknown variable {name!r}")


# --- assign variable ---
def assign_variable(name: str, value: AST, indent: int, lctx: dict):
    # -- check EXIST --
    block = ""

    if name in lctx:
        var_name = lctx[name]
    else:
        var_name = "$" + name
        lctx[name] = var_name

    value_block = generate(value, indent, lctx)
    assert value_block

    block += value_block + LF()
    block += TABs(indent) + "local.set " + var_name + LF()

    return block


def generate_variable_block(tree, indent, lctx):
    block = ""
    for key in lctx.keys():
        var_name = lctx[key]
        block += TABs(indent) + "(local " + var_name + " i32)" + LF()

    return block
