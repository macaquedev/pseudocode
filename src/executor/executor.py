from ..lexer import Lexer
from ..parser import Parser
from ..interpreter import Interpreter
from ..interpreter.context import Context
from ..interpreter.symbol_table import SymbolTable

from typing import List
from ..builtins.ps_builtins import populate_builtins


class PSCodeExecutor:
    def __init__(self):
        self.parser = Parser()
        self.global_symbol_table = SymbolTable()
        self.context = Context("<main>")
        self.context.symbol_table = self.global_symbol_table
        populate_builtins(self.context.symbol_table)
        self.interpreter = Interpreter()

    def execute(self, filename: str, code: str, args: List[str]):
        if code.strip() == "":
            return

        lexer = Lexer(filename, code.strip())
        tokens, error = lexer.lex_line()

        if error:
            print(error)
            return

        self.parser.initialize(tokens)
        ast = self.parser.parse()
        if ast.error:
            print(ast.error)
            return
        result = self.interpreter.visit(ast.node, self.context)
        if result.error:
            print(result.error)
