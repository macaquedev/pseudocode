from ..interpreter.interpreter import PythonFunction, Number, String, List, Boolean, Null
from .iostream import ps_print, ps_input


def populate_builtins(symbol_table):
    builtins = {
        "NULL": Null()
    }
    symbol_table.symbols.update(builtins)
