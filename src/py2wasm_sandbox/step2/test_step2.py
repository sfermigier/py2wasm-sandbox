from .compiler import compile


def test_add():
    prog = "1 + 2"
    compile(prog)


def test_add_many():
    prog = "1 + 2 + (3 + (4 + 5) )"
    compile(prog)


def test_binary_op():
    prog = "(1 + 3*5 - 4/2) % 3"
    compile(prog)
