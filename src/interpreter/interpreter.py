import re
from typing import Callable
from .runtime_result import RTResult
from .context import Context
from .symbol_table import SymbolTable
from ..errors import NotImplementedError, RuntimeError, InvalidSyntaxError
from ..lexer.tokens import KeywordToken
from ..parser.nodes import (
    NumberNode, StringNode, BooleanNode, BinOpNode,
    UnaryOpNode, VarAssignNode, VarAccessNode,
    IfNode, ListNode, ForNode, ListIndexNode, NullNode
)


class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()
        self.start_position = None
        self.end_position = None
        self.context = None

    def illegal_operation(self, other=None, message=None):
        if other is None and message is None:
            return RuntimeError(
                self.start_position, self.end_position.copy().advance(),
                f"{self.start_position.ftxt} evaluates to a {self.__class__.__name__}"
                f"{f' with value {self.value}' if hasattr(self, 'value') else ''}, not a function, "
                f"therefore it cannot be called.",
                self.context
            )
        return RuntimeError(
            self.start_position, other.end_position,
            f"Invalid operands for {message}: {self.__class__.__name__} and {other.__class__.__name__}", self.context
        )

    def set_pos(self, start_position=None, end_position=None):
        self.start_position = start_position
        self.end_position = end_position
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def __add__(self, other):
        return None, self.illegal_operation(other, "addition")

    def __sub__(self, other):
        return None, self.illegal_operation(other, "subtraction")

    def __mul__(self, other):
        return None, self.illegal_operation(other, "multiplication")

    def __truediv__(self, other):
        return None, self.illegal_operation(other, "division")

    def __floordiv__(self, other):
        return None, self.illegal_operation(other, "floor division")

    def __mod__(self, other):
        return None, self.illegal_operation(other, "modulo division")

    def __eq__(self, other):
        return None, self.illegal_operation(other, "'==' operator")

    def __ne__(self, other):
        return None, self.illegal_operation(other, "'!=' operator")

    def __gt__(self, other):
        return None, self.illegal_operation(other, "'>' operator")

    def __lt__(self, other):
        return None, self.illegal_operation(other, "'<' operator")

    def __ge__(self, other):
        return None, self.illegal_operation(other, "'>=' operator")

    def __le__(self, other):
        return None, self.illegal_operation(other, "'<=' operator")

    def __call__(self, args):
        return RTResult().failure(self.illegal_operation())

    def __getitem__(self, other):
        return None, RuntimeError(
            other.start_position, other.end_position,
            f"Cannot get item from a {self.__class__.__name__}",
            self.context
        )


class Null(Value):
    def __init__(self):
        super().__init__()
        self.value = None

    def __repr__(self):
        return "null"

    def __str__(self):
        return "null"

    def copy(self):
        return self


class List(Value):
    def __init__(self, elements: any):
        super().__init__()
        self.elements = elements

    def __add__(self, other):
        if isinstance(other, List):
            return List(self.elements + other.elements), None
        else:
            return List(self.elements + [other]), None

    def copy(self):
        return List(self.elements).set_pos(self.start_position, self.end_position).set_context(self.context)

    def __repr__(self):
        return f"List({self.elements})"

    def __str__(self):
        return f"{[str(i) for i in self.elements]}"  # TODO

    def __getitem__(self, other):
        if other.__class__.__name__ == "Number":
            if other.value == (x := int(other.value)):
                if -len(self.elements) <= x < len(self.elements):
                    return self.elements[x], None
                else:
                    return None, RuntimeError(
                        other.start_position, other.end_position,
                        f"List index {x} out of range, valid indexes range from "
                        f"{-len(self.elements)} to {len(self.elements) - 1} inclusive.",
                        self.context
                    )
            else:
                return None, RuntimeError(
                    other.start_position, other.end_position,
                    "Cannot get decimal index from a list",
                    self.context
                )
        return None, RuntimeError(
            other.start_position, other.end_position,
            f"Cannot get {other.__class__.__name__} index from a list",
            self.context
        )


class Boolean(Value):
    def __init__(self, value: bool):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"Boolean({self.value})"

    def __str__(self):
        return "true" if self.value else "false"

    def __eq__(self, other):
        if isinstance(other, Boolean):
            return Boolean(other.value == self.value).set_context(self.context), None
        elif isinstance(other, Number):
            if other.value == 0:
                return Boolean(self.value).set_context(self.context), None
            else:
                return Boolean(not self.value).set_context(self.context), None

    def __ne__(self, other):
        if isinstance(other, Boolean):
            return Boolean(other.value != self.value).set_context(self.context), None
        elif isinstance(other, Number):
            if other.value == 0:
                return Boolean(not self.value).set_context(self.context), None
            else:
                return Boolean(self.value).set_context(self.context), None

    def anded_by(self, other):
        if isinstance(other, Boolean):
            return Boolean(other.value and self.value).set_context(self.context), None
        elif isinstance(other, Number):
            if other.value == 0:
                return Boolean(False).set_context(self.context), None
            else:
                return Boolean(self.value).set_context(self.context), None

    def ored_by(self, other):
        if isinstance(other, Boolean):
            return Boolean(other.value or self.value).set_context(self.context), None
        elif isinstance(other, Number):
            if other.value == 0:
                return Boolean(self.value).set_context(self.context), None
            else:
                return Boolean(True).set_context(self.context), None

    def __bool__(self):
        return self.value

    def copy(self):
        return Boolean(self.value).set_pos(self.start_position, self.end_position).set_context(self.context)


class Number(Value):
    def __init__(self, value: float):
        super().__init__()
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"

    def __str__(self):
        return str(x) if (x := int(self.value)) == self.value else self.value

    def __add__(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "addition")

    def __sub__(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "subtraction")

    def __mul__(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "multiplication")

    def __truediv__(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(
                    self.start_position, other.end_position,
                    "Division by zero.", self.context
                )
            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "division")

    def __floordiv__(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(
                    self.start_position, other.end_position,
                    "Floor division by zero.", self.context
                )
            return Number(float(self.value // other.value)).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "floor division")

    def __mod__(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RuntimeError(
                    self.start_position, other.end_position,
                    "Modulo division by zero.", self.context
                )
            elif other.value != int(other.value):
                return None, RuntimeError(
                    self.start_position, other.end_position,
                    "Modulo division by a decimal number.", self.context
                )
            return Number(float(self.value % other.value)).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "modulo division")

    def __pow__(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "power operator")

    def __eq__(self, other):
        if isinstance(other, Number):
            return Boolean(self.value == other.value), None
        else:
            return Boolean(False), None

    def __ne__(self, other):
        if isinstance(other, Number):
            return Boolean(self.value != other.value), None
        else:
            return Boolean(True), None

    def __gt__(self, other):
        if isinstance(other, Number):
            return Boolean(self.value > other.value), None
        else:
            return None, self.illegal_operation(other, "'>' operator")

    def __lt__(self, other):
        if isinstance(other, Number):
            return Boolean(self.value < other.value), None
        else:
            return None, self.illegal_operation(other, "'<' operator")

    def __ge__(self, other):
        if isinstance(other, Number):
            return Boolean(self.value >= other.value), None
        else:
            return None, self.illegal_operation(other, "'>=' operator")

    def __le__(self, other):
        if isinstance(other, Number):
            return Boolean(self.value <= other.value), None
        else:
            return None, self.illegal_operation(other, "'<=' operator")

    def __bool__(self):
        return self.value != 0

    def copy(self):
        return Number(self.value).set_pos(self.start_position, self.end_position).set_context(self.context)


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def __add__(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        else:
            return None, self.illegal_operation(other, "string concatenation")

    def __mul__(self, other):
        if isinstance(other, Number):
            if other.value == (x := int(other.value)):
                return String(self.value * x).set_context(self.context), None
            else:
                return None, RuntimeError(
                    other.start_position, other.end_position,
                    "Cannot multiply a string by a decimal number", self.context
                )
        else:
            return None, self.illegal_operation(other, "string multiplication")

    def __eq__(self, other):
        if isinstance(other, String):
            return Boolean(self.value == other.value), None
        else:
            return Boolean(False), None

    def __ne__(self, other):
        if isinstance(other, String):
            return Boolean(self.value != other.value), None
        else:
            return Boolean(True), None

    def __gt__(self, other):
        if isinstance(other, String):
            return Boolean(self.value > other.value), None
        else:
            return None, self.illegal_operation(other, "'>' operator")

    def __lt__(self, other):
        if isinstance(other, String):
            return Boolean(self.value < other.value), None
        else:
            return None, self.illegal_operation(other, "'<' operator")

    def __ge__(self, other):
        if isinstance(other, String):
            return Boolean(self.value >= other.value), None
        else:
            return None, self.illegal_operation(other, "'>=' operator")

    def __le__(self, other):
        if isinstance(other, String):
            return Boolean(self.value <= other.value), None
        else:
            return None, self.illegal_operation(other, "'<=' operator")

    def __bool__(self):
        return len(self.value) > 0

    def __repr__(self):
        return f"String({self.value})"

    def __str__(self):
        return str(self.value)

    def copy(self):
        return String(self.value).set_pos(self.start_position, self.end_position).set_context(self.context)


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.start_position)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        if len(args) != len(arg_names):
            return RTResult().failure(RuntimeError(
                self.start_position, self.end_position,
                f"Invalid number of arguments passed to function.\n"
                f"You passed {len(args)} arguments. The function expects {len(arg_names)} arguments.",
                self.context
            ))

        return RTResult().success(None)

    @staticmethod
    def populate_args(arg_names, args, exec_ctx):
        for name, value in zip(arg_names, args):
            exec_ctx.symbol_table.set(name, value.set_context(exec_ctx))

    def check_and_populate_args(self, arg_names, args, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.should_return():
            return res
        self.populate_args(arg_names, args, exec_ctx)
        return res.success(None)

    def __repr__(self):
        return f"<function {self.name}>"


class PSFunction(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return

    def __call__(self, args):
        res = RTResult()
        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()
        res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        if res.should_return() and res.func_return_value is None:
            return res

        return res.success((value if self.should_auto_return else None)
                           or res.func_return_value or exec_ctx.symbol_table.get("null"))

    def copy(self):
        return PSFunction(self.name, self.body_node, self.arg_names, self.should_auto_return).set_context(
            self.context).set_pos(self.start_position, self.end_position)

    def __repr__(self):
        return f"<function {self.name}>"


class PythonFunction(BaseFunction):
    def __init__(self, name, body, arg_names):
        super().__init__(name)
        self.body = body
        self.arg_names = arg_names

    def __call__(self, args):
        res = RTResult()
        exec_ctx = self.generate_new_context()
        self.check_and_populate_args(self.arg_names, args, exec_ctx)
        return_value = self.body(exec_ctx.symbol_table)
        if res.should_return():
            return res

        return res.success(return_value)

    def copy(self):
        return PythonFunction(self.name, self.body, self.arg_names).set_pos(
            self.start_position, self.end_position).set_context(self.context)


class Interpreter:
    @staticmethod
    def get_method_name(method_name: str):
        return "visit_" + "_".join([i.lower() for i in re.findall("[A-Z][^A-Z]*", method_name)])

    def visit(self, node: any, context: Context) -> object:
        method_name = self.get_method_name(type(node).__name__)
        method: Callable = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node: any, context: Context):
        return RTResult().failure(NotImplementedError(
            node.start_position, node.end_position,
            f"No {self.get_method_name(node.__class__.__name__)} method defined\n"
            "This means that the developer of this calamity has messed up.\n"
            "Please email me at macaquedev@gmail.com or create an issue on Github so that I can fix this as soon as possible.",
            context
        ))

    @staticmethod
    def visit_number_node(node: NumberNode, context: Context) -> RTResult:
        return RTResult().success(
            Number(node.tok.value).set_context(context).set_pos(node.start_position, node.end_position)
        )

    @staticmethod
    def visit_string_node(node: StringNode, context: Context) -> RTResult:
        return RTResult().success(
            String(node.tok.value).set_context(context).set_pos(node.start_position, node.end_position)
        )

    @staticmethod
    def visit_boolean_node(node: BooleanNode, context: Context) -> RTResult:
        return RTResult().success(
            Boolean(node.tok.value == "true").set_context(context).set_pos(node.start_position, node.end_position)
        )

    @staticmethod
    def visit_null_node(node: NullNode, context: Context) -> RTResult:
        return RTResult().success(
            context.symbol_table.get("null").set_pos(node.start_position, node.end_position)
        )

    def visit_list_node(self, node: ListNode, context: Context) -> RTResult:
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res
            
        return res.success(
            List(elements).set_context(context).set_pos(node.start_position, node.end_position)
        )

    def visit_list_index_node(self, node: ListIndexNode, context: Context) -> RTResult:
        res = RTResult()
        list_instance = res.register(self.visit(node.list_instance, context))
        if res.should_return():
            return res
        index = res.register(self.visit(node.index, context))
        if res.should_return():
            return res

        result, error = list_instance[index]
        if error:
            return res.failure(error)
        return res.success(result)

    def visit_bin_op_node(self, node: BinOpNode, context: Context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        right = res.register(self.visit(node.right_node, context))
        if res.should_return():
            return res
        if node.op_tok.__class__.__name__ == "PlusToken":
            result, error = left + right
        elif node.op_tok.__class__.__name__ == "MinusToken":
            result, error = left - right
        elif node.op_tok.__class__.__name__ == "MultiplyToken":
            result, error = left * right
        elif node.op_tok.__class__.__name__ == "DivideToken":
            result, error = left / right
        elif node.op_tok.__class__.__name__ == "FloorDivideToken":
            result, error = left // right
        elif node.op_tok.__class__.__name__ == "PowerToken":
            result, error = left ** right
        elif node.op_tok.__class__.__name__ == "ModuloToken":
            result, error = left % right
        elif node.op_tok.__class__.__name__ == "EqualsToken":
            result, error = left == right
        elif node.op_tok.__class__.__name__ == "NotEqualsToken":
            result, error = left != right
        elif node.op_tok.__class__.__name__ == "GreaterThanToken":
            result, error = left > right
        elif node.op_tok.__class__.__name__ == "LessThanToken":
            result, error = left < right
        elif node.op_tok.__class__.__name__ == "GreaterThanOrEqualsToken":
            result, error = left >= right
        elif node.op_tok.__class__.__name__ == "LessThanOrEqualsToken":
            result, error = left <= right
        elif node.op_tok.__class__.__name__ == "KeywordToken" and node.op_tok.value == "and":
            result, error = left.anded_by(right)
        elif node.op_tok.__class__.__name__ == "KeywordToken" and node.op_tok.value == "or":
            result, error = left.ored_by(right)
        else:
            result, error = None, None
        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.start_position, node.end_position))

    def visit_unary_op_node(self, node: UnaryOpNode, context: Context):
        res = RTResult()
        operand = res.register(self.visit(node.node, context))

        if res.should_return():
            return res

        if operand.__class__.__name__ == "Number":
            if node.op_tok.__class__.__name__ == "MinusToken":
                operand, error = operand * Number(-1)
            elif node.op_tok.__class__.__name__ == "PlusToken":
                pass
        elif operand.__class__.__name__ == "Boolean":
            if node.op_tok.matches(KeywordToken("not")):
                operand.value = not operand.value

        return res.success(operand.set_pos(node.start_position, node.end_position))

    @staticmethod
    def visit_var_access_node(node: VarAccessNode, context: Context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)
        if value is None:
            return res.failure(RuntimeError(
                node.start_position, node.end_position,
                f"'{var_name}' is not defined.", context
            ))

        return res.success(value.copy().set_pos(node.start_position, node.end_position).set_context(context))

    def visit_var_assign_node(self, node: VarAssignNode, context: Context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res
        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_if_node(self, node: IfNode, context: Context):
        res = RTResult()

        for condition, expr, should_auto_return in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res

            if condition_value.__class__.__name__ in ["Number", "Boolean"]:
                if condition_value:
                    expr_value = res.register(self.visit(expr, context))
                    if res.should_return():
                        return res
                    return res.success(expr_value if not should_auto_return else context.symbol_table.get("null"))
            else:
                return res.failure(InvalidSyntaxError(
                    node.start_position, node.end_position,
                    "Invalid case - must evaluate to Boolean or Number."
                ))

        if node.else_case:
            expr, should_auto_return = node.else_case
            else_value = res.register(self.visit(expr, context))
            if res.should_return():
                return res
            return res.success(else_value if not should_auto_return else context.symbol_table.get("null"))

        return res.success(context.symbol_table.get("null"))

    def visit_for_node(self, node: ForNode, context: Context) -> RTResult:
        res = RTResult()
        elements = []
        start_value = res.register(self.visit(node.start_value_node, context))
        if res.should_return():
            return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return():
            return res

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
            if res.should_return():
                return res
        else:
            step_value = Number(1.0)

        i = start_value

        if step_value >= Number(0):
            def condition():
                return (i < end_value)[0]
        else:
            def condition():
                return (i > end_value)[0]

        context.symbol_table.set(node.var_name_tok.value, i)

        while condition():
            context.symbol_table.set(node.var_name_tok.value, i)
            i, _ = i + step_value

            value = res.register(self.visit(node.body_node, context))
            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        return res.success(List(elements).set_context(context).set_pos(node.start_position, node.end_position)
                           if not node.should_auto_return
                           else context.symbol_table.get("null"))

    def visit_while_node(self, node, context):
        res = RTResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res

            if not condition:
                break

            value = res.register(self.visit(node.body_node, context))

            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                continue

            elements.append(value)

        return res.success(
            List(elements).set_context(context).set_pos(node.start_position, node.end_position)
            if node.should_auto_return
            else context.symbol_table.get("null")
        )

    @staticmethod
    def visit_func_def_node(node, context):
        res = RTResult()
        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        func_value = PSFunction(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_pos(
            node.start_position, node.end_position)

        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    def visit_call_node(self, node, context):
        res = RTResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        value_to_call = value_to_call.copy().set_pos(node.start_position, node.end_position)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res

        return_value = res.register(value_to_call(args))
        if res.should_return():
            return res
        return res.success(return_value.copy().set_pos(node.start_position, node.end_position).set_context(context))

    def visit_return_node(self, node, context):
        res = RTResult()

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res
        else:
            value = context.symbol_table.get("null")
        return res.success_return(value or context.symbol_table.get("null"))

    @staticmethod
    def visit_continue_node(*_):
        return RTResult().success_continue()

    @staticmethod
    def visit_break_node(*_):
        return RTResult().success_continue()
