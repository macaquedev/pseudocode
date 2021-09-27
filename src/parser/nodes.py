from src.lexer.tokens import IdentifierToken


class NumberNode:
    def __init__(self, tok: any):
        self.tok = tok
        self.start_position = self.tok.start_position
        self.end_position = self.tok.end_position

    def __repr__(self):
        return f'{self.tok}'


class StringNode(NumberNode):
    pass


class BooleanNode(NumberNode):
    pass


class NullNode(NumberNode):
    pass


class BinOpNode:
    def __init__(self, left_node: any, op_tok: any, right_node: any):
        self.left_node = left_node
        self.right_node = right_node
        self.op_tok = op_tok
        self.start_position = self.left_node.start_position
        self.end_position = self.right_node.end_position

    def __repr__(self):
        return f'({self.left_node} {self.op_tok} {self.right_node})'


class UnaryOpNode:
    def __init__(self, op_tok: any, node: any):
        self.op_tok = op_tok
        self.node = node
        self.start_position = op_tok.start_position
        self.end_position = node.end_position

    def __repr__(self):
        return f'({self.op_tok} {self.node})'


class ListNode:
    def __init__(self, element_nodes, start_position, end_position):
        self.element_nodes = element_nodes
        self.start_position = start_position
        self.end_position = end_position

    def __repr__(self):
        return f'{self.element_nodes}'


class VarAccessNode:
    def __init__(self, var_name_tok: IdentifierToken):
        self.var_name_tok = var_name_tok
        self.start_position = var_name_tok.start_position
        self.end_position = var_name_tok.end_position

    def __repr__(self):
        return f'VarAccess({self.var_name_tok})'


class VarAssignNode:
    def __init__(self, var_name_tok: IdentifierToken, value_node: any):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.start_position = var_name_tok.start_position
        self.end_position = var_name_tok.end_position

    def __repr__(self):
        return f'VarAssign({self.var_name_tok})'


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        self.start_position = self.cases[0][0].start_position
        self.end_position = (self.else_case or self.cases[-1])[0].end_position

    def __repr__(self):
        return f'IfNode({self.cases}, {self.else_case})'


class ForNode:
    def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node, should_auto_return):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        self.start_position = self.var_name_tok.start_position
        self.end_position = self.body_node.end_position

    def __repr__(self):
        return f"ForNode({self.start_value_node}, {self.end_value_node}, {self.step_value_node}){{{self.body_node}}}"


class WhileNode:
    def __init__(self, condition_node, body_node, should_auto_return):
        self.should_auto_return = should_auto_return
        self.condition_node = condition_node
        self.body_node = body_node

        self.start_position = self.condition_node.start_position
        self.end_position = self.body_node.end_position

    def __repr__(self):
        return f"WhileNode({self.condition_node}){{{self.body_node}}}"


class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, body_node, should_auto_return):
        self.should_auto_return = should_auto_return
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.body_node = body_node

        if self.var_name_tok:
            self.start_position = self.var_name_tok.start_position
        elif len(self.arg_name_toks) > 0:
            self.start_position = self.arg_name_toks[0].start_position
        else:
            self.start_position = self.body_node.start_position

        self.end_position = self.body_node.end_position

    def __repr__(self):
        return f"FuncDefNode({self.arg_name_toks}){{{self.body_node}}}"


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.start_position = self.node_to_call.start_position

        if len(self.arg_nodes) > 0:
            self.end_position = self.arg_nodes[-1].end_position.copy().advance()
        else:
            self.end_position = self.node_to_call.end_position.copy().advance()

    def __repr__(self):
        return f"Call({self.node_to_call}({self.arg_nodes}))"


class ListIndexNode:
    def __init__(self, list_instance, index):
        self.list_instance = list_instance
        self.index = index
        self.start_position = self.list_instance.start_position
        self.end_position = self.index.end_position.copy().advance()

    def __repr__(self):
        return f"{self.list_instance}[{self.index}]"


class ReturnNode:
    def __init__(self, node_to_return, start_position, end_position):
        self.node_to_return = node_to_return
        self.start_position = start_position
        self.end_position = end_position

    def __repr__(self):
        return f"ReturnNode({self.node_to_return})"


class ContinueNode:
    def __init__(self, start_position, end_position):
        self.start_position = start_position
        self.end_position = end_position

    def __repr__(self):
        return "ContinueNode"


class BreakNode:
    def __init__(self, start_position, end_position):
        self.start_position = start_position
        self.end_position = end_position

    def __repr__(self):
        return "BreakNode"
