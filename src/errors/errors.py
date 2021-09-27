class BasePSError:
    def __init__(self, start_position, end_position, error_type, error_message, context):
        self.start_position = start_position
        self.end_position = end_position
        self.error_type = error_type
        self.error_message = error_message
        self.context = context

    def generate_traceback(self):
        result = ""
        prev_line = ""
        count = 1
        pos = self.start_position
        context = self.context

        while context:
            line = f'  File {pos.filename}, line {str(pos.line + 1)}, in {context.display_name}'
            if line == prev_line:
                count += 1
            else:
                if count == 1:
                    result = line + "\n" + result
                else:
                    result = line + "\n" + result[:result.index("\n")] + f' (x{count})' + result[result.index("\n"):]
                count = 1
            pos = context.parent_entry_pos
            context = context.parent
            prev_line = line
        return "Traceback (most recent call last):\n" + result

    def __repr__(self):
        idx_start = max(self.start_position.ftxt.rfind('\n', 0, self.start_position.index), 0)
        idx_end = self.start_position.ftxt.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(self.start_position.ftxt)

        line = self.start_position.ftxt[idx_start:idx_end]
        return (self.generate_traceback()
                + "    "
                + line[1:self.start_position.column + 1]
                + line[self.start_position.column + 1:self.end_position.column + 1]
                + line[self.end_position.column + 1:]
                + "\n    " + "-" * self.start_position.column
                + "~" * (self.end_position.column - self.start_position.column)
                + "-" * (len(line) - self.end_position.column - 1)
                + f"\npscode > ERROR: {self.error_type}\n"
                + f'{self.error_message}'
                )


class IllegalCharError:
    def __init__(self, position, char):
        self.position = position
        self.char = char

    def __repr__(self):
        idx_start = max(self.position.ftxt.rfind('\n', 0, self.position.index), 0)
        idx_end = self.position.ftxt.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(self.position.ftxt)

        line = self.position.ftxt[idx_start:idx_end]
        return (f"pscode > ERROR: Illegal Character '{self.char}'\n"
                f'  File "{self.position.filename}", line {self.position.line + 1}'
                + "\n    "
                + line[1:self.position.column + 1]
                + line[self.position.column + 1]
                + line[self.position.column + 2:]
                + "\n    " + "-" * self.position.column + "^" + (len(line) - self.position.column - 1) * "-")


class ExpectedCharError:
    def __init__(self, position, details):
        self.position = position
        self.details = details

    def __repr__(self):
        idx_start = max(self.position.ftxt.rfind('\n', 0, self.position.index), 0)
        idx_end = self.position.ftxt.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(self.position.ftxt)

        line = self.position.ftxt[idx_start:idx_end]
        return (f"pscode > ERROR: {self.details}\n"
                f'  File "{self.position.filename}", line {self.position.line + 1}'
                + "\n    "
                + line[1:self.position.column + 1]
                + line[self.position.column + 1]
                + line[self.position.column + 2:]
                + "\n    " + "-" * self.position.column + "^" + (len(line) - self.position.column - 1) * "-")


class UnexpectedEOFError:
    def __init__(self, position, details):
        self.position = position
        self.details = details

    def __repr__(self):
        idx_start = max(self.position.ftxt.rfind('\n', 0, self.position.index), 0)
        idx_end = self.position.ftxt.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(self.position.ftxt)

        line = self.position.ftxt[idx_start:idx_end][1:]
        return (f"pscode > ERROR: Unexpected EOF while parsing string\n"
                + self.details
                + f'\n  File "{self.position.filename}", line {self.position.line + 1}'
                + "\n    "
                + line + "\n    "
                + "-" * (len(line)) + "^")


class InvalidSyntaxError:
    def __init__(self, start_position, end_position, error_message):
        self.start_position = start_position.copy()
        self.end_position = end_position.copy()
        self.error_message = error_message

    def __repr__(self):
        idx_start = max(self.start_position.ftxt.rfind('\n', 0, self.start_position.index), 0)
        idx_end = self.start_position.ftxt.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(self.start_position.ftxt)

        line = self.start_position.ftxt[idx_start:idx_end]
        return (f"pscode > ERROR: Invalid Syntax\n"
                f'{self.error_message}\n'
                f'  File "{self.start_position.filename}", line {self.start_position.line + 1}'
                + "\n    "
                + line[:self.start_position.column]
                + line[self.start_position.column:self.end_position.column]
                + line[self.end_position.column:]
                + "\n    " + "-" * self.start_position.column
                + "~" * (self.end_position.column - self.start_position.column)
                + "-" * (len(line) - self.end_position.column))


class RuntimeError(BasePSError):
    def __init__(self, start_position, end_position, error_message, context):
        super().__init__(start_position, end_position, "Runtime Error", error_message, context)


class NotImplementedError(BasePSError):
    def __init__(self, start_position, end_position, error_message, context):
        super().__init__(start_position, end_position, "Not Implemented", error_message, context)

