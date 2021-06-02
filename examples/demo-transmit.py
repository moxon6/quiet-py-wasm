from quiet_py_wasm import Quiet
import sys

while True:
    Quiet().transmit(
        sys.argv[1] + "\n",
        "audible"
    )
