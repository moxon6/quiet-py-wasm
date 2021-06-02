from quiet_py_wasm import Quiet

for res in Quiet().receive("audible"):
    print(res, end='')
