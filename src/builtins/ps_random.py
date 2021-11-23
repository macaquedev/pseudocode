import random
from ..interpreter.interpreter import Number


def rand_between(symbol_table):
    value1 = symbol_table.get("value1")
    value2 = symbol_table.get("value2")
    return Number(random.randint(value1.value, value2.value))