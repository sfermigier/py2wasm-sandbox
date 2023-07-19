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
