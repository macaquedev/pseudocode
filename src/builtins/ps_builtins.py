from ..interpreter.interpreter import PythonFunction, Number, String, List, Boolean, Null
from .conversions import to_int, to_string, to_bool, to_real
from .ps_random import rand_between

def populate_builtins(symbol_table):
    builtins = {
        "NULL": Null(),
        "INT": PythonFunction("INT", to_int, ["value"]),
        "STRING": PythonFunction("STRING", to_string, ["value"]),
        "BOOL": PythonFunction("BOOL", to_bool, ["value"]),
        "REAL": PythonFunction("REAL", to_real, ["value"]),
        "RANDBETWEEN": PythonFunction("RANDBETWEEN", rand_between, ["value1", "value2"]),
    }
    symbol_table.symbols.update(builtins)
