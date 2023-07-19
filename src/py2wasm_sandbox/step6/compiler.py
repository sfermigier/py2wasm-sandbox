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
# - 04: compare operator (===, !==, <, > <=, >=)
# - 05: if
#   - 05: if
#   - 05: if-else
# - 05: while
# - 06: Refactor block generation

import ast
from ast import AST

from devtools import debug


class Block:
    def __init__(self, lines=None):
        if lines:
            self.lines = list(lines)
        else:
            self.lines = []
        self.indentation: int = 0

    def __lshift__(self, other):
        match other:
            case str(line):
                self.lines += ["  " * self.indentation + line]
            case Block():
                block = other
                assert block.indentation == 0
                for line in block.lines:
                    self << line
            case _:
                raise ValueError(f"Unknown type: {type(other)}")

    def indent(self):
        self.indentation += 1

    def dedent(self):
        self.indentation -= 1

    def __str__(self):
        return "\n".join(self.lines)


def compile(source: str) -> str:
    root = ast.parse(source)
    wat = compile_tree(root)
    return wat


def compile_tree(tree) -> str:
    lctx = {}
    main_block = generate(tree, lctx)
    var_block = generate_variable_block(tree, lctx)

    block = Block()
    block << "(module"
    block.indent()
    block << '(import "env" "js_putn" (func $putn (param i32)))'
    block << '(export "exported_main" (func $main))'
    block << "(func $main (result i32)"
    block.indent()
    block << var_block
    block << main_block
    block << "return"
    block.dedent()
    block << ")"
    block.dedent()
    block << ")"

    return str(block)


def generate(tree: AST | list[AST], lctx) -> Block:
    match tree:
        case ast.Module(body):
            return generate(body, lctx)

        case [*nodes]:
            return Block(generate(node, lctx) for node in nodes)

        case ast.Expr(value):
            return generate(value, lctx)

        case ast.Constant(value):
            return generate(value, lctx)

        case ast.BinOp(left, op, right):
            left_block = generate(left, lctx)
            right_block = generate(right, lctx)
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

            block = Block()
            block << left_block
            block << right_block
            block << wasm_op
            return block

        case ast.Compare(left, ops, comparators):
            left_block = generate(left, lctx)
            op = ops[0]
            right = comparators[0]
            right_block = generate(right, lctx)
            match op:
                case ast.Eq():
                    wasm_op = "i32.eq"
                case ast.NotEq():
                    wasm_op = "i32.ne"
                case ast.Lt():
                    wasm_op = "i32.lt_s"
                case ast.LtE():
                    wasm_op = "i32.le_s"
                case ast.Gt():
                    wasm_op = "i32.gt_s"
                case ast.GtE():
                    wasm_op = "i32.ge_s"
                case _:
                    raise NotImplementedError(f"Unknown operator {op!r}")

            block = Block()
            block.indent()
            block << left_block
            block << right_block
            block << wasm_op
            block.dedent()
            return block

        case int(n):
            return Block([f"i32.const {n}"])

        case ast.Call(func, args):
            match func:
                case ast.Name(id="putn"):
                    return generateCallPutn(args, lctx)
                case _:
                    raise ValueError(f"Unknown function {func!r}")

        case ast.Assign(targets, value):
            assert len(targets) == 1
            target = targets[0]
            assert isinstance(target, ast.Name)
            name = target.id
            return assign_variable(name, value, lctx)

        case ast.Name(id):
            return refer_variable(id, lctx)

        case ast.If(test, body, orelse):
            test_block = generate(test, lctx)
            body_block = generate(body, lctx)

            block = Block()
            block << test_block
            block << "if"
            block.indent()
            block << body_block
            block.dedent()

            if orelse:
                orelse_block = generate(orelse, lctx)
                block << "else"
                block.indent()
                block << orelse_block
                block.dedent()

            block << "end"

            return block

        case ast.While(test, body, orelse):
            test_block = generate(test, lctx)
            body_block = generate(body, lctx)

            debug(test_block.lines, test_block.indentation)

            block = Block()
            block << "loop ;; begin of while loop"
            block << test_block
            block.indent()
            block << "if"
            block.indent()
            block << body_block
            block << "br 1 ;; jump to head of while loop"
            block.dedent()
            block << "end ;; end of if-then"
            block.dedent()
            block << "end ;; end of while loop"

            return block

        case _:
            raise NotImplementedError(f"Unknown node {tree!r}")


def generateCallPutn(args, lctx) -> Block:
    """Debug function"""
    value_block = generate(args, lctx)
    assert value_block

    block = Block()
    block << value_block
    block << "call $putn"

    return block


# --- refer variable ---
def refer_variable(name, lctx) -> Block:
    # -- check EXIST --
    if name in lctx:
        var_name = lctx[name]
        block = Block(["local.get " + var_name])

        return block

    raise ValueError(f"Unknown variable {name!r}")


def assign_variable(name: str, value: AST, lctx: dict):
    if name in lctx:
        var_name = lctx[name]
    else:
        var_name = "$" + name
        lctx[name] = var_name

    value_block = generate(value, lctx)
    assert value_block

    block = Block()
    block << value_block
    block << "local.set " + var_name

    return block


def generate_variable_block(tree, lctx) -> Block:
    block = Block()
    for key in lctx.keys():
        var_name = lctx[key]
        block << "(local " + var_name + " i32)"

    return block
