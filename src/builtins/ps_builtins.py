from ..interpreter.interpreter import PythonFunction, Number, String, List, Boolean, Null
from .iostream import ps_print, ps_input


def populate_builtins(symbol_table):
    builtins = {
        "null": Null(),
        "print": PythonFunction("print", ps_print, ["value"]),
        "input": PythonFunction("input", ps_input, ["prompt"])
    }
    symbol_table.symbols.update(builtins)
