import os
from wasmer import engine, Store, Module, Instance, ImportObject, Function, FunctionType, Type
from wasmer_compiler_cranelift import Compiler
import json
import time
from .transmitter import Transmitter
from .utils import encode

quiet_dir = os.path.dirname(__file__)

quiet_path = os.path.join(quiet_dir, "quiet.wasm")
profiles_path = os.path.join(quiet_dir, "quiet-profiles.json")

class Quiet:
    def __init__(self):
        self.profiles = json.load(open(profiles_path, 'r'))
        self.instance = self._build_instance()

    
    def _build_instance(self):
        import_object = ImportObject()

        store = Store(engine.JIT(Compiler))

        import_object.register(
            "env",
            {
            "__sys_getpid": Function(store, lambda: 42, FunctionType([], [Type.I32] )),
            }
        )

        import_object.register(
            "wasi_snapshot_preview1",
            {
            "proc_exit": Function(store, lambda *args: None, FunctionType([Type.I32], [] )),
            "clock_time_get": Function(store, lambda *args: int(time.time()), FunctionType([Type.I32, Type.I64, Type.I32], [Type.I32])),
            "fd_close": Function(store, lambda *args: 1, FunctionType([Type.I32], [Type.I32] )),
            "fd_write": Function(store, lambda *args: 1, FunctionType([Type.I32,Type.I32,Type.I32,Type.I32], [Type.I32] )),
            "fd_seek": Function(store, lambda *args: 1, FunctionType([Type.I32, Type.I64, Type.I32, Type.I32], [Type.I32])),
            "fd_read": Function(store, lambda *args: 1, FunctionType([Type.I32, Type.I32, Type.I32, Type.I32], [Type.I32])),
            }
        )

        # Let's compile the module to be able to execute it!
        module = Module(store, open(quiet_path, 'rb').read())

        # Now the module is compiled, we can instantiate it.
        return Instance(module, import_object)
    
    def transmit(self, payload, profile, clampFrame):
        Transmitter(self.instance) \
            .select_profile(self.profiles[profile], clampFrame) \
            .transmit(encode(payload)) \
            .destroy()