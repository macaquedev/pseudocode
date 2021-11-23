from ..interpreter.interpreter import Number, String, Boolean

def to_int(symbol_table):
    value = symbol_table.get("value")
    return Number(int(value.value))

def to_string(symbol_table):
    value = symbol_table.get("value")
    return String(str(value.value))

def to_bool(symbol_table):
    value = symbol_table.get("value")
    return Boolean(bool(value.value))

def to_real(symbol_table):
    value = symbol_table.get("value")
    return Number(value.value)