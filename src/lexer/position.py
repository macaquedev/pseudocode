from dataclasses import dataclass


@dataclass
class Position:
    index: int
    line: int
    column: int
    filename: str
    ftxt: str

    def advance(self, current_char=None):
        self.index += 1
        self.column += 1

        if current_char == "\n":
            self.line += 1
            self.column = 0

        return self

    def copy(self):
        return Position(self.index, self.line, self.column, self.filename, self.ftxt)
