// run_wasi.js
//  refer https://nodejs.org/api/wasi.html
//
// node --experimental-wasi-unstable-preview0 run_wasi.js your_wasi.wasm

"use strict";

const fs = require("fs");

const filename = process.argv[2]; // the name of the wasm file to be executed
console.warn("Loading wasm/wasi file: " + filename);

const { WASI } = require("wasi");
const wasi = new WASI({
  args: process.argv,
  env: process.env,
  preopens: {
    //'/sandbox': '/some/real/path/that/wasm/can/access'
  },
});
const importObject = { wasi_unstable: wasi.wasiImport };

(async () => {
  const wasm = await WebAssembly.compile(fs.readFileSync(filename)).catch(
    (err) => {
      console.log(err);
      process.exit(1);
    }
  );
  const instance = await WebAssembly.instantiate(wasm, importObject).catch(
    (err) => {
      console.log(err);
      process.exit(2);
    }
  );

  wasi.start(instance);
})();
