import subprocess
from pathlib import Path

import pywasm

from .compiler import compile

# language=python
PROG = """
1 == 1
1 != 1
1 < 1
1 <= 1
1 > 1
1 >= 1
"""


def test_prog():
    wat = compile(PROG)
    Path("generated.wat").write_text(wat)
    subprocess.check_call(["wat2wasm", "generated.wat"])
    runtime = pywasm.load("generated.wasm")
    runtime.exec("exported_main", [])
