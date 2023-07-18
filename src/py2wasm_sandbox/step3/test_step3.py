import subprocess
from pathlib import Path

import pywasm

from .compiler import compile

# language=python
PROG = """
putn(1) # 1

# --- declare variable ---
a = 1 + 2 + 3
putn(a) # 6

# --- assigne variable, refer variable ---
b = a + 1
b = b + 2
putn(b)  # 9
putn(a + b * 2) # 24

b # expect 9
"""


def test_putn():
    compile("putn(1)")


def test_prog():
    wat = compile(PROG)
    Path("generated.wat").write_text(wat)
    subprocess.check_call(["wat2wasm", "generated.wat"])
    runtime = pywasm.load("generated.wasm")
    runtime.exec("exported_main", [])
