from ..errors import IllegalCharError, ExpectedCharError, UnexpectedEOFError
from .tokens import (
    PlusToken, IncrementToken, MinusToken,
    DecrementToken, MultiplyToken, MultiplyIncrementToken,
    DivideToken, DivideDecrementToken, FloorDivideToken,
    FloorDivideDecrementToken, PowerToken, CommaToken,
    ModuloToken, AssignmentToken, ArrowToken,
    NumberToken, IdentifierToken, KeywordToken,
    LParenToken, RParenToken, LSquareToken, RSquareToken,
    LCurlyToken, RCurlyToken, EOFToken, EqualsToken,
    NotEqualsToken, LessThanOrEqualsToken,
    LessThanToken, GreaterThanOrEqualsToken, 
    GreaterThanToken, StringToken, NewlineToken,
    ColonToken
)
from ..keywords import keywords
from .position import Position
from string import ascii_letters


class Lexer:
    def __init__(self, filename: str, text: str):
        self.filename = filename
        self.text = text.strip()
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        self.escape_chars = {
            "n": "\n",
            "t": "\t",
            "r": "\r"
        }
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

    def lex_line(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in ";\n":
                tokens.append(NewlineToken(start_position=self.pos))
                self.advance()
            elif self.current_char in "1234567890.":
                tokens.append(self.make_number())
            elif self.current_char in ascii_letters:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                result, error = self.make_string()
                if error:
                    return [], error
                else:
                    tokens.append(result)
            elif self.current_char == "=":
                start_position = self.pos.copy()
                self.advance()
                if self.current_char == ">":
                    tokens.append(ArrowToken(start_position=start_position, end_position=self.pos))
                    self.advance()
                else:
                    tokens.append(EqualsToken(start_position=start_position))
            elif self.current_char == "<":
                start_position = self.pos.copy()
                self.advance()
                if self.current_char == "=":
                    tokens.append(LessThanOrEqualsToken(start_position=start_position, end_position=self.pos))
                    self.advance()
                elif self.current_char == ">":
                    tokens.append(NotEqualsToken(start_position=start_position, end_position=self.pos))
                    self.advance()
                elif self.current_char == "-":
                    tokens.append(AssignmentToken(start_position=start_position, end_position=self.pos))
                    self.advance()
                else:
                    tokens.append(LessThanToken(start_position=start_position))
            elif self.current_char == ">":
                start_position = self.pos.copy()
                self.advance()
                if self.current_char == "=":
                    tokens.append(GreaterThanOrEqualsToken(start_position=start_position, end_position=self.pos))
                    self.advance()
                else:
                    tokens.append(GreaterThanToken(start_position=start_position))
            elif self.current_char == ',':
                tokens.append(CommaToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '+':
                tokens.append(PlusToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(MinusToken(start_position=self.pos))
                self.advance()
            elif self.current_char == "%":
                tokens.append(ModuloToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '*':
                start_position = self.pos.copy()
                self.advance()
                if self.current_char == "*":
                    self.advance()
                    tokens.append(PowerToken(start_position=start_position, end_position=self.pos))
                else:
                    tokens.append(MultiplyToken(start_position=start_position))

            elif self.current_char == '/':
                start_position = self.pos.copy()
                self.advance()
                if self.current_char == "/":
                    tokens.append(FloorDivideToken(start_position=start_position, end_position=self.pos))
                    self.advance()
                else:
                    tokens.append(DivideToken(start_position=start_position))
            elif self.current_char == ':':
                tokens.append(ColonToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(LParenToken(start_position=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(RParenToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(LSquareToken(start_position=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(RSquareToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '{':
                tokens.append(LCurlyToken(start_position=self.pos))
                self.advance()
            elif self.current_char == '}':
                tokens.append(RCurlyToken(start_position=self.pos))
                self.advance()
            else:
                start_position = self.pos.copy()
                char = self.current_char
                return [], IllegalCharError(start_position, char)

        tokens.append(EOFToken(start_position=self.pos))
        return tokens, None

    def make_string(self):
        value = ""
        terminator = self.current_char
        escaped = False
        start_position = self.pos.copy()
        self.advance()
        while True:
            if self.current_char == terminator:
                break
            if self.current_char == "\\":
                escaped = True
                self.advance()
            if self.current_char is None:
                return None, UnexpectedEOFError(start_position, "This probably means you have forgotten to close a string")
            if escaped:
                value += self.escape_chars.get(self.current_char, self.current_char)
                escaped = False
            else:
                value += self.current_char
            self.advance()
            
        self.advance()
        return StringToken(value, start_position=start_position, end_position=self.pos), None

    def make_number(self):
        num_str = ''
        dot_count = 0
        start_position = self.pos.copy()

        while self.current_char is not None and self.current_char in "0123456789.":
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        return NumberToken(float(num_str), start_position, self.pos)

    def make_identifier(self):
        id_str = ""
        start_position = self.pos.copy()

        while self.current_char and self.current_char in "0123456789_" + ascii_letters:
            id_str += self.current_char
            self.advance()

        if id_str == "MOD":
            return ModuloToken(id_str, start_position=start_position, end_position=self.pos)
        elif id_str in keywords:
            return KeywordToken(id_str, start_position=start_position, end_position=self.pos)
        else:
            return IdentifierToken(id_str, start_position=start_position, end_position=self.pos)

    def make_not_equals(self):
        start_position = self.pos.copy()
        self.advance()

        if self.current_char == "=":
            self.advance()
            return NotEqualsToken(start_position=start_position, end_position=self.pos), None

        return None, ExpectedCharError(
            self.pos,
            "Expected '=' after '!'"
        )
