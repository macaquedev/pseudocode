from typing import List, Callable, Union, Tuple
from .nodes import (
    NumberNode, BooleanNode, StringNode, BinOpNode, UnaryOpNode, VarAssignNode,
    VarAccessNode, IfNode, ForNode, WhileNode, FuncDefNode, CallNode, ListNode, ListIndexNode, NullNode, ReturnNode,
    ContinueNode, BreakNode, RepeatNode, CaseNode,
    PrintNode, InputNode
)
from ..errors import InvalidSyntaxError
from ..lexer.tokens import KeywordToken
from .parse_result import ParseResult


class Parser:
    def __init__(self):
        self.tokens = None
        self.tok_idx = None
        self.current_tok = None

    def initialize(self, tokens: List[any]):
        self.tokens = tokens
        self.tok_idx = -1
        self.current_tok = None
        self.advance()

    def advance(self):
        self.tok_idx += 1
        self.update_current_tok()

    def reverse(self, amount: int = 1):
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self):
        if 0 <= self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    def parse(self):
        res = self.statements()
        if not (res.error or self.current_tok.__class__.__name__ == "EOFToken"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected '+', '-', '*', '/', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"
            ))

        return res

    def statements(self):
        res = ParseResult()
        statements = []
        start_position = self.current_tok.start_position.copy()

        self.allow_zero_or_more_new_lines(res)

        statement = res.register(self.statement())
        if res.error:
            return res

        statements.append(statement)

        more_statements = True

        while True:
            newline_count = self.allow_zero_or_more_new_lines(res)

            if newline_count == 0:
                more_statements = False

            if not more_statements:
                break

            if self.current_tok.__class__.__name__ == "KeywordToken" and self.current_tok.value in ["ELIF", "ELSE", "ENDIF", "ENDWHILE", "UNTIL", "NEXT", "ENDCASE", "ENDPROCEDURE"]:
                self.reverse()
                more_statements = False
                continue

            statement = res.register(self.statement())
            if res.error:
                return res

            statements.append(statement)

        return res.success(ListNode(statements, start_position, self.current_tok.end_position.copy()))

    def statement(self):
        res = ParseResult()
        start_position = self.current_tok.start_position.copy()

        if self.current_tok.matches(KeywordToken("RETURN")):
            res.register_advancement()
            self.advance()

            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, start_position, self.current_tok.start_position.copy()))

        elif self.current_tok.matches(KeywordToken("CONTINUE")):
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(start_position, self.current_tok.start_position.copy()))

        elif self.current_tok.matches(KeywordToken("BREAK")):
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(start_position, self.current_tok.start_position.copy()))

        elif self.current_tok.matches(KeywordToken("PRINT")):
            objects_to_print = []
            res.register_advancement()
            self.advance()

            expr = res.register(self.expr())
            if res.error:
                return res

            objects_to_print.append(expr)

            while self.current_tok.__class__.__name__ == "CommaToken":
                res.register_advancement()
                self.advance()

                expr = res.register(self.expr())
                if res.error:
                    return res
                objects_to_print.append(expr)

            if self.current_tok.__class__.__name__ not in ["NewlineToken", "EOFToken"]:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected newline or comma"
                ))

            return res.success(PrintNode(
                objects_to_print, 
                start_position, self.current_tok.start_position.copy()
            ))

        elif self.current_tok.matches(KeywordToken("INPUT")):
            res.register_advancement()
            self.advance()

            if self.current_tok.__class__.__name__ != "IdentifierToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected variable name"
                ))
            
            var_name_tok = self.current_tok

            res.register_advancement()
            self.advance()

            return res.success(InputNode(var_name_tok, start_position, self.current_tok.start_position.copy()))

        elif self.current_tok.__class__.__name__ == "IdentifierToken":
            var_name_tok = self.current_tok
            self.advance()

            if self.current_tok.__class__.__name__ == "AssignmentToken":
                res.register_advancement()
                res.register_advancement()
                self.advance()

                expr = res.register(self.expr())

                if res.error:
                    return res

                return res.success(VarAssignNode(var_name_tok, expr))

            self.reverse()
            
        expr = res.register(self.expr())
        if res.error:
            return res

        return res.success(expr)

    def expr(self):
        res = ParseResult()
        node = res.register(self.bin_op(self.comp_expr, [("KeywordToken", "AND"), ("KeywordToken", "OR")]))
        if res.error:
            return res

        return res.success(node)

    def comp_expr(self):
        res = ParseResult()
        if self.current_tok.matches(KeywordToken("NOT")):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(self.bin_op(self.arith_expr, [
            "EqualsToken", "NotEqualsToken", "LessThanToken",
            "GreaterThanToken", "LessThanOrEqualsToken", "GreaterThanOrEqualsToken"]))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected number, identifier, '+', '-', '(', '[' or 'not'",
            ))

        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, ["PlusToken", "MinusToken"])

    def term(self):
        return self.bin_op(self.factor, ["MultiplyToken", "DivideToken", "FloorDivideToken", "ModuloToken"])

    def factor(self):
        res = ParseResult()
        tok = self.current_tok
        if tok.__class__.__name__ in ["PlusToken", "MinusToken"]:
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, ["PowerToken"], self.factor)

    def call(self):
        res = ParseResult()
        list_index = res.register(self.list_index())
        if res.error:
            return res

        if self.current_tok.__class__.__name__ == "LParenToken":
            res.register_advancement()
            self.advance()
            arg_nodes = []
            if self.current_tok.__class__.__name__ == "RParenToken":
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.start_position, self.current_tok.end_position,
                        "Expected ')', 'IF', 'FOR', 'WHILE', 'REPEAT', 'CASE', 'PROCEDURE', "
                        "number, identifier, '+', '-', '(', '[' or 'NOT'"
                    ))

                while self.current_tok.__class__.__name__ == "CommaToken":
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res

                if self.current_tok.__class__.__name__ != "RParenToken":
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.start_position, self.current_tok.end_position,
                        "Expected ',' or ')"
                    ))

                res.register_advancement()
                self.advance()

            return res.success(CallNode(list_index, arg_nodes))
        return res.success(list_index)

    def list_index(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res

        if self.current_tok.__class__.__name__ == "LSquareToken":
            res.register_advancement()
            self.advance()

            index = res.register(self.expr())

            if self.current_tok.__class__.__name__ != "RSquareToken":
                return res.failure(InvalidSyntaxError(
                    atom.start_position, self.current_tok.end_position,
                    "Expected ']'"
                ))

            res.register_advancement()
            self.advance()
            return res.success(ListIndexNode(atom, index))
        return res.success(atom)

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.__class__.__name__ == "NumberToken":
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(tok))
        if tok.__class__.__name__ == "StringToken":
            res.register_advancement()
            self.advance()
            return res.success(StringNode(tok))
        elif tok.__class__.__name__ == "IdentifierToken":
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(tok))
        elif tok.__class__.__name__ == "KeywordToken" and tok.value in {"TRUE", "FALSE"}:
            res.register_advancement()
            self.advance()
            return res.success(BooleanNode(tok))
        elif tok.matches(KeywordToken("NULL")):
            res.register_advancement()
            self.advance()
            return res.success(NullNode(tok))
        elif tok.__class__.__name__ == "LParenToken":
            res.register_advancement()
            self.advance()
            expression = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.__class__.__name__ == "RParenToken":
                res.register_advancement()
                self.advance()
                return res.success(expression)
            else:
                return res.failure(InvalidSyntaxError(
                    tok.start_position, tok.end_position,
                    "Expected ')'. This probably means that you haven't closed a parenthesis you have opened."
                ))
        elif tok.__class__.__name__ == "LSquareToken":
            list_expr = res.register(self.list_expr())
            if res.error:
                return res
            return res.success(list_expr)
        elif tok.matches(KeywordToken('IF')):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)
        elif tok.matches(KeywordToken('FOR')):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)
        elif tok.matches(KeywordToken('WHILE')):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)
        elif tok.matches(KeywordToken('REPEAT')):
            repeat_expr = res.register(self.repeat_expr())
            if res.error:
                return res
            return res.success(repeat_expr)
        elif tok.matches(KeywordToken('CASE')):
            case_expr = res.register(self.case_expr())
            if res.error:
                return res
            return res.success(case_expr)
        elif tok.matches(KeywordToken('FUNCTION')):
            while_expr = res.register(self.func_def())
            if res.error:
                return res
            return res.success(while_expr)

        return res.failure(InvalidSyntaxError(
            tok.start_position, tok.end_position,
            "Expected number, identifier, '+', '-', '(', '[', 'if', 'for', 'while' or 'function'",
        ))

    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        start_position = self.current_tok.start_position.copy()

        if self.current_tok.__class__.__name__ != "LSquareToken":
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                f"Expected '['"
            ))

        res.register_advancement()
        self.advance()
        if self.current_tok.__class__.__name__ == "RSquareToken":
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected ']', 'IF', 'FOR', 'WHILE', 'REPEAT', 'CASE', 'PROCEDURE', "
                    "number, identifier, '+', '-', '(', '[' or 'NOT'"
                ))

            while self.current_tok.__class__.__name__ == "CommaToken":
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.__class__.__name__ != "RSquareToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected ',' or ']"
                ))

            res.register_advancement()
            self.advance()

        return res.success(ListNode(element_nodes, start_position, self.current_tok.end_position.copy()))

    def if_expr(self):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_tok.matches(KeywordToken("IF")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'IF'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        self.allow_zero_or_more_new_lines(res)

        if not self.current_tok.matches(KeywordToken("THEN")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'THEN'"
            ))
        res.register_advancement()
        self.advance()
        self.allow_zero_or_more_new_lines(res)

        body = res.register(self.statements())

        if res.error:
            return res

        cases.append((condition, body, False))
        self.allow_zero_or_more_new_lines(res)
        while self.current_tok.matches(KeywordToken("ELIF")):
            res.register_advancement()
            self.advance()

            condition = res.register(self.expr())
            if res.error:
                return res

            self.allow_zero_or_more_new_lines(res)

            if not self.current_tok.matches(KeywordToken("THEN")):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected 'THEN'"
                ))

            res.register_advancement()
            self.advance()
            self.allow_zero_or_more_new_lines(res)

            body = res.register(self.statements())

            if res.error:
                return res
            
            cases.append((condition, body, False))

        if self.current_tok.matches(KeywordToken("ELSE")):
            res.register_advancement()
            self.advance()
            self.allow_zero_or_more_new_lines(res)

            body = res.register(self.statements())
            if res.error:
                return res
            
            else_case = (body, False)
            self.allow_zero_or_more_new_lines(res)

        if not self.current_tok.matches(KeywordToken("ENDIF")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'ENDIF'"
            ))


        res.register_advancement()
        self.advance()

        return res.success(IfNode(cases, else_case))

    def case_expr(self):
        res = ParseResult()
        cases = []

        if not self.current_tok.matches(KeywordToken("CASE")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'CASE'"
            ))

        res.register_advancement()
        self.advance()

        if not self.current_tok.matches(KeywordToken("OF")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'OF'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.__class__.__name__ != "IdentifierToken":
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected identifier (variable name)"
            ))

        var_name = self.current_tok
        res.register_advancement()
        self.advance()
        self.allow_zero_or_more_new_lines(res)

        if res.error:
            return res

        if self.current_tok.__class__.__name__ == "KeywordToken" and self.current_tok.value in ["ENDCASE", "OTHERWISE"]:
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                f"Expected case before {self.current_tok.value}"
            ))

        while self.current_tok.__class__.__name__ != "IdentifierToken" and self.current_tok.value not in ["ENDCASE", "OTHERWISE"]:
            value = res.register(self.expr())
            if res.error:
                return res
                
            if self.current_tok.__class__.__name__ != "ColonToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected colon"
                ))

            res.register_advancement() 
            self.advance()

            response = res.register(self.statement())
            if res.error:
                return res

            res.register_advancement()
            self.advance()
            self.allow_zero_or_more_new_lines(res)

            cases.append((value, response, False))

        self.allow_zero_or_more_new_lines(res)

        if self.current_tok.matches(KeywordToken("ENDCASE")):
            res.register_advancement()
            self.advance()

            return res.success(CaseNode(var_name, cases, None))

        elif self.current_tok.matches(KeywordToken("OTHERWISE")):
            res.register_advancement() 
            self.advance()

            if self.current_tok.__class__.__name__ != "ColonToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected colon"
                ))

            res.register_advancement() 
            self.advance()

            response = res.register(self.statement())
            if res.error:
                return res
            
            res.register_advancement()
            self.advance()
            self.allow_zero_or_more_new_lines(res)

            if not self.current_tok.matches(KeywordToken("ENDCASE")):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected 'ENDCASE'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(CaseNode(var_name, cases, (response, False)))
        
        else:
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected case, 'OTHERWISE' or 'ENDCASE'"
            ))


    def for_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(KeywordToken("FOR")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'FOR'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.__class__.__name__ != "IdentifierToken":
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected identifier (variable name)"
            ))

        var_name = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.__class__.__name__ != "AssignmentToken":
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected '<-'"
            ))

        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error:
            return res

        if not self.current_tok.matches(KeywordToken('TO')):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'TO'"
            ))

        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.matches(KeywordToken('STEP')):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error:
                return res

        else:
            step_value = None

        res.register_advancement()
        self.advance()
        self.allow_zero_or_more_new_lines(res)

        body = res.register(self.statements())
        if res.error:
            return res
        
        if not self.current_tok.matches(KeywordToken('NEXT')):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'NEXT'"
            ))

        res.register_advancement()
        self.advance()

        if not self.current_tok.matches(var_name):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                f"Expected '{var_name.value}'"
            ))

        res.register_advancement()
        self.advance()

        return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(KeywordToken("WHILE")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'WHILE'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        res.register_advancement()
        self.advance()
        self.allow_zero_or_more_new_lines(res)

        body = res.register(self.statements())
        if res.error:
            return res

        if not self.current_tok.matches(KeywordToken("ENDWHILE")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'ENDWHILE'"
            ))
        res.register_advancement()
        self.advance()

        return res.success(WhileNode(condition, body, True))

    def repeat_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(KeywordToken("REPEAT")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'REPEAT'"
            ))

        res.register_advancement()
        self.advance()
        self.allow_zero_or_more_new_lines(res)

        body = res.register(self.statements())
        if res.error:
            return res

        if not self.current_tok.matches(KeywordToken("UNTIL")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'UNTIL'"
            ))
            
        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error:
            return res

        res.register_advancement()
        self.advance()

        return res.success(RepeatNode(condition, body, True))

    def func_def(self):
        res = ParseResult()

        if not self.current_tok.matches(KeywordToken("FUNCTION")):
            return res.failure(InvalidSyntaxError(
                self.current_tok.start_position, self.current_tok.end_position,
                "Expected 'function' keyword"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.__class__.__name__ == "IdentifierToken":
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.__class__.__name__ != "LParenToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected '('"
                ))

        else:
            var_name_tok = None
            if self.current_tok.__class__.__name__ != "LParenToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected identifier or '('"
                ))

        res.register_advancement()
        self.advance()
        arg_name_toks = []

        if self.current_tok.__class__.__name__ == "IdentifierToken":
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()

            while self.current_tok.__class__.__name__ == "CommaToken":
                res.register_advancement()
                self.advance()

                if self.current_tok.__class__.__name__ != "IdentifierToken":
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.start_position, self.current_tok.end_position,
                        "Expected identifier"
                    ))

                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

            if self.current_tok.__class__.__name__ != "RParenToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected ',' or ')'"
                ))

        else:
            if self.current_tok.__class__.__name__ != "RParenToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected ',' or ')'"
                ))

        res.register_advancement()
        self.advance()
        if self.current_tok.__class__.__name__ == "ArrowToken":
            res.register_advancement()
            self.advance()

            node_to_return = res.register(self.expr())
            if res.error:
                return res

            return res.success(FuncDefNode(var_name_tok, arg_name_toks, node_to_return, True))

        else:
            self.allow_zero_or_more_new_lines(res)
            if self.current_tok.__class__.__name__ != "LCurlyToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected '=>' or '{'"
                ))

            res.register_advancement()
            self.advance()
            self.allow_zero_or_more_new_lines(res)

            body = res.register(self.statements())
            if res.error:
                return res

            if self.current_tok.__class__.__name__ != "RCurlyToken":
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start_position, self.current_tok.end_position,
                    "Expected '}'"
                ))

            res.register_advancement()
            self.advance()
            return res.success(FuncDefNode(var_name_tok, arg_name_toks, body, False))

    def bin_op(self, func: Callable, ops: List[Union[str, Tuple[str, str]]], func2: Callable = None):
        if not func2:
            func2 = func
        res = ParseResult()
        left = res.register(func())
        if res.error:
            return res

        while self.current_tok.__class__.__name__ in ops or (self.current_tok.__class__.__name__, self.current_tok.value) in ops:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func2())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)

    def allow_zero_or_more_new_lines(self, res):
        count = 0
        while self.current_tok.__class__.__name__ == "NewlineToken":
            res.register_advancement()
            self.advance()
            count += 1

        return count
