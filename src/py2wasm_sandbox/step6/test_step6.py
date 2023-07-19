import subprocess
from pathlib import Path

import pywasm

from .compiler import compile

# language=python
PROG = """
if 1:
    putn(1)

if 0:
    putn(2)
else:
    putn(3)

i = 0
while i < 10:
    i = i + 1

0
"""


def test_prog():
    wat = compile(PROG)
    Path("generated.wat").write_text(wat)
    subprocess.check_call(["wat2wasm", "generated.wat"])
    runtime = pywasm.load("generated.wasm")
    runtime.exec("exported_main", [])
