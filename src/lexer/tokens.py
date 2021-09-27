from .position import Position


class BaseToken:
    def __init__(self, value: any = None, start_position: Position = None, end_position: Position = None):
        self.start_position = None
        self.end_position = None
        self.value = value

        if end_position and start_position:
            self.start_position = start_position.copy()
            self.end_position = end_position.copy()
        elif start_position:
            self.start_position = start_position.copy()
            self.end_position = start_position.copy()
            self.end_position.advance()

    def matches(self, other):
        return self.__class__.__name__ == other.__class__.__name__ and self.value == other.value

    def __repr__(self):
        if self.value:
            try:
                return f"[{self.__class__.__name__}({self.value}) at [{self.start_position.line + 1}:{self.start_position.column + 1}]]"
            except AttributeError:
                return f"[{self.__class__.__name__}({self.value}) at [UNKNOWN]]"
        else:
            try:
                return f"[{self.__class__.__name__} at [{self.start_position.line + 1}:{self.start_position.column + 1}]]"
            except AttributeError:
                return f"[{self.__class__.__name__} at [UNKNOWN]]"


class PlusToken(BaseToken):
    pass


class IncrementToken(BaseToken):
    pass


class MinusToken(BaseToken):
    pass


class DecrementToken(BaseToken):
    pass


class MultiplyToken(BaseToken):
    pass


class MultiplyIncrementToken(BaseToken):
    pass


class DivideToken(BaseToken):
    pass


class PowerToken(BaseToken):
    pass


class ModuloToken(BaseToken):
    pass


class FloorDivideToken(BaseToken):
    pass


class DivideDecrementToken(BaseToken):
    pass


class FloorDivideDecrementToken(BaseToken):
    pass


class LParenToken(BaseToken):
    pass


class RParenToken(BaseToken):
    pass


class LSquareToken(BaseToken):
    pass


class RSquareToken(BaseToken):
    pass


class EOFToken(BaseToken):
    pass


class AssignmentToken(BaseToken):
    pass


class EqualsToken(BaseToken):
    pass


class NotEqualsToken(BaseToken):
    pass


class GreaterThanToken(BaseToken):
    pass


class LessThanToken(BaseToken):
    pass


class GreaterThanOrEqualsToken(BaseToken):
    pass


class LessThanOrEqualsToken(BaseToken):
    pass


class NumberToken(BaseToken):
    pass


class IdentifierToken(BaseToken):
    pass


class KeywordToken(BaseToken):
    pass


class CommaToken(BaseToken):
    pass


class ArrowToken(BaseToken):
    pass


class StringToken(BaseToken):
    pass


class NewlineToken(BaseToken):
    pass


class LCurlyToken(BaseToken):
    pass


class RCurlyToken(BaseToken):
    pass
