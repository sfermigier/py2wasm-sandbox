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

# language=javascript
JS = """
const fs = require("fs");
const bytes = fs.readFileSync(__dirname + "/generated.wasm");

let exported_main = null; // function will be set later

let importObject = {
  env: {
    js_putn: function (n) {
      console.log(n);
    },
  },
};

(async () => {
  let obj = await WebAssembly.instantiate(new Uint8Array(bytes), importObject);
  ({ exported_main: exported_main } = obj.instance.exports);
  exported_main();
})();
"""


def test_prog():
    wat = compile(PROG)
    Path("tmp/generated.wat").write_text(wat)
    subprocess.check_call(["wat2wasm", "-o", "tmp/generated.wasm", "tmp/generated.wat"])
    Path("tmp/generated.js").write_text(JS)
    subprocess.check_call(["node", "tmp/generated.js"])
