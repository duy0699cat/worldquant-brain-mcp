"""Deterministic parsing and AST similarity helpers for Brain expressions."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Any


TOKEN_PATTERN = re.compile(
    r"""\s*(
    (?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
    |(?P<name>[A-Za-z_][A-Za-z0-9_]*)
    |(?P<operator>==|!=|<=|>=|&&|\|\||[+\-*/%^(),<>])
    )""",
    re.VERBOSE,
)


@dataclass(frozen=True)
class ExpressionNode:
    kind: str
    value: str
    children: tuple["ExpressionNode", ...] = ()


class BrainExpressionSyntaxError(ValueError):
    """Raised when a Brain expression cannot be parsed into an AST."""


@lru_cache(maxsize=4096)
def parse_expression(expression: str) -> ExpressionNode:
    parser = _ExpressionParser(expression)
    node = parser.parse()
    return node


def try_parse_expression(expression: str) -> tuple[ExpressionNode | None, str | None]:
    try:
        return parse_expression(expression), None
    except BrainExpressionSyntaxError as exc:
        return None, str(exc)


def describe_expression(
    expression: str,
    node: ExpressionNode | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    parsed_node = node
    error = parse_error
    if parsed_node is None and error is None:
        parsed_node, error = try_parse_expression(expression)

    if parsed_node is None:
        return {
            "summary": None,
            "steps": [],
            "fields": [],
            "functions": [],
            "parseError": error,
        }

    return {
        "summary": _summarize_expression(parsed_node),
        "steps": _build_steps(parsed_node),
        "fields": _collect_fields(parsed_node),
        "functions": _collect_functions(parsed_node),
        "parseError": None,
    }


def tree_size(node: ExpressionNode) -> int:
    return 1 + sum(tree_size(child) for child in node.children)


def largest_common_subtree_size(left: ExpressionNode, right: ExpressionNode) -> int:
    best = 0
    right_nodes = tuple(_walk_nodes(right))
    for left_node in _walk_nodes(left):
        for right_node in right_nodes:
            best = max(best, _rooted_common_subtree_size(left_node, right_node))
    return best


def ast_similarity(left: ExpressionNode, right: ExpressionNode) -> float:
    smaller = min(tree_size(left), tree_size(right))
    if smaller == 0:
        return 0.0
    return largest_common_subtree_size(left, right) / smaller


def _walk_nodes(node: ExpressionNode):
    yield node
    for child in node.children:
        yield from _walk_nodes(child)


def _rooted_common_subtree_size(left: ExpressionNode, right: ExpressionNode) -> int:
    if left.kind != right.kind or len(left.children) != len(right.children):
        return 0
    if left.kind != "number" and left.value != right.value:
        return 0
    child_sizes = [_rooted_common_subtree_size(left_child, right_child) for left_child, right_child in zip(left.children, right.children)]
    if any(child_size == 0 for child_size in child_sizes):
        return 1 if not left.children else 0
    return 1 + sum(child_sizes)


class _ExpressionParser:
    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.tokens = self._tokenize(expression)
        self.index = 0

    def parse(self) -> ExpressionNode:
        node = self._parse_expression(0)
        if self._peek() is not None:
            token = self._peek()
            raise BrainExpressionSyntaxError(
                f"Unexpected token '{token.value}' at position {token.position} in expression: {self.expression}"
            )
        return node

    def _parse_expression(self, min_precedence: int) -> ExpressionNode:
        node = self._parse_unary()
        while True:
            token = self._peek()
            if token is None or token.kind != "operator" or token.value not in _INFIX_PRECEDENCE:
                break
            precedence = _INFIX_PRECEDENCE[token.value]
            if precedence < min_precedence:
                break
            operator = self._consume().value
            right = self._parse_expression(precedence + 1)
            node = ExpressionNode("binary", operator, (node, right))
        return node

    def _parse_unary(self) -> ExpressionNode:
        token = self._peek()
        if token is not None and token.kind == "operator" and token.value in {"+", "-"}:
            operator = self._consume().value
            operand = self._parse_expression(_UNARY_PRECEDENCE)
            return ExpressionNode("unary", operator, (operand,))
        return self._parse_primary()

    def _parse_primary(self) -> ExpressionNode:
        token = self._peek()
        if token is None:
            raise BrainExpressionSyntaxError(f"Unexpected end of expression: {self.expression}")
        if token.kind == "name":
            name = self._consume().value
            if self._match("operator", "("):
                args: list[ExpressionNode] = []
                if not self._match("operator", ")"):
                    while True:
                        args.append(self._parse_expression(0))
                        if self._match("operator", ")"):
                            break
                        self._expect("operator", ",")
                return ExpressionNode("call", name.lower(), tuple(args))
            return ExpressionNode("name", name.lower())
        if token.kind == "number":
            return ExpressionNode("number", self._consume().value)
        if token.kind == "operator" and token.value == "(":
            self._consume()
            node = self._parse_expression(0)
            self._expect("operator", ")")
            return node
        raise BrainExpressionSyntaxError(
            f"Unexpected token '{token.value}' at position {token.position} in expression: {self.expression}"
        )

    def _peek(self) -> "_Token | None":
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _consume(self) -> "_Token":
        token = self._peek()
        if token is None:
            raise BrainExpressionSyntaxError(f"Unexpected end of expression: {self.expression}")
        self.index += 1
        return token

    def _match(self, kind: str, value: str) -> bool:
        token = self._peek()
        if token is None or token.kind != kind or token.value != value:
            return False
        self.index += 1
        return True

    def _expect(self, kind: str, value: str) -> None:
        if not self._match(kind, value):
            token = self._peek()
            actual = token.value if token is not None else "end of expression"
            position = token.position if token is not None else len(self.expression)
            raise BrainExpressionSyntaxError(
                f"Expected '{value}' at position {position}, found '{actual}' in expression: {self.expression}"
            )

    def _tokenize(self, expression: str) -> list["_Token"]:
        tokens: list[_Token] = []
        position = 0
        while position < len(expression):
            match = TOKEN_PATTERN.match(expression, position)
            if not match:
                character = expression[position]
                if character.isspace():
                    position += 1
                    continue
                raise BrainExpressionSyntaxError(
                    f"Unexpected character '{character}' at position {position} in expression: {expression}"
                )
            value = match.group(0).strip()
            if not value:
                position = match.end()
                continue
            kind = "number" if match.group("number") else "name" if match.group("name") else "operator"
            tokens.append(_Token(kind=kind, value=value, position=position))
            position = match.end()
        return tokens


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    position: int


_INFIX_PRECEDENCE = {
    "||": 1,
    "&&": 2,
    "==": 3,
    "!=": 3,
    "<": 4,
    "<=": 4,
    ">": 4,
    ">=": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
    "%": 6,
    "^": 7,
}
_UNARY_PRECEDENCE = 8

FIELD_ALIASES = {
    "implied_volatility_put_10": "10-day at-the-money put implied volatility",
    "implied_volatility_put_120": "120-day at-the-money put implied volatility",
    "implied_volatility_mean_skew_30": "30-day mean implied-volatility skew",
    "snt1_d1_dynamicfocusrank": "dynamic focus-rank sentiment signal",
    "snt1_cored1_score": "core daily sentiment score",
    "anl4_qf_az_eps_mean": "analyst EPS mean estimate",
    "anl4_qf_az_dts_spe": "analyst EPS estimate dispersion",
    "anl4_mark": "broker recommendation marker",
    "receivable": "receivables",
    "inventory": "inventory",
    "sales": "sales",
    "cogs": "cost of goods sold",
    "cashflow_op": "operating cash flow",
    "income": "income",
    "employee": "employee count",
    "return_on_invested_capital_4": "return on invested capital",
    "mdl177_v1_400_ttmaccu": "mdl177 trailing accruals factor",
    "mdl177_earningsqualityfactor_ttmaccu_alt": "mdl177 alternative trailing accrual-quality factor",
    "mdl177_2_managementqualityfactor_ocfroi": "mdl177 operating cash-flow return on investment factor",
    "mdl177_2_managementqualityfactor_fcfroi": "mdl177 free cash-flow return on investment factor",
    "mdl177_2_managementqualityfactor_noato": "mdl177 net operating asset turnover factor",
    "mdl177_2_managementqualityfactor_opmb": "mdl177 operating margin factor",
    "mdl177_2_managementqualityfactor_ocfmargin": "mdl177 operating cash-flow margin factor",
    "mdl177_2_5yearrelativevaluefactor_rel5ycfp": "mdl177 5-year relative cash-flow-to-price factor",
    "mdl177_2_5yearrelativevaluefactor_rel5ydivp": "mdl177 5-year relative dividend-to-price factor",
}


def _summarize_expression(node: ExpressionNode) -> str:
    phrase = _describe_node(node)
    return f"This expression computes the {phrase}."


def _build_steps(node: ExpressionNode) -> list[str]:
    steps = _collect_steps(node)
    deduped = list(dict.fromkeys(step for step in steps if step))
    return deduped[:8]


def _collect_steps(node: ExpressionNode) -> list[str]:
    if node.kind != "call":
        return []

    if node.value in {"rank", "ts_rank", "ts_zscore", "ts_delta", "ts_backfill", "ts_decay_linear", "ts_mean", "ts_std_dev", "reverse", "zscore", "abs", "vec_avg"} and node.children:
        base_steps = _collect_steps(node.children[0])
        step = _describe_step(node)
        return base_steps + ([step] if step else [])

    return [_describe_step(node)] if _describe_step(node) else []


def _describe_step(node: ExpressionNode) -> str:
    if node.kind != "call":
        return ""

    if node.value == "add":
        return "Combine the component signals by addition."
    if node.value == "ts_backfill" and len(node.children) >= 2:
        return f"Backfill missing values in {_describe_node(node.children[0])} using up to {_literal_text(node.children[1])} days of history."
    if node.value == "ts_delta" and len(node.children) >= 2:
        return f"Measure the change in {_describe_node(node.children[0])} over {_literal_text(node.children[1])} days."
    if node.value == "ts_zscore" and len(node.children) >= 2:
        return f"Normalize the signal as a {_literal_text(node.children[1])}-day time-series z-score."
    if node.value == "ts_decay_linear" and len(node.children) >= 2:
        return f"Linearly smooth the signal over {_literal_text(node.children[1])} days."
    if node.value == "ts_mean" and len(node.children) >= 2:
        return f"Average the signal over {_literal_text(node.children[1])} days."
    if node.value == "ts_rank" and len(node.children) >= 2:
        return f"Rank the signal against its own {_literal_text(node.children[1])}-day history."
    if node.value == "rank" and node.children:
        return "Cross-sectionally rank the resulting signal."
    if node.value == "reverse" and node.children:
        return "Flip the sign of the signal."
    if node.value == "zscore" and node.children:
        return "Cross-sectionally z-score the signal."
    if node.value == "ts_std_dev" and len(node.children) >= 2:
        return f"Measure the {_literal_text(node.children[1])}-day standard deviation of the signal."
    return f"Apply {node.value} to build the signal."


def _describe_node(node: ExpressionNode) -> str:
    if node.kind == "name":
        return FIELD_ALIASES.get(node.value, node.value.replace("_", " "))
    if node.kind == "number":
        return node.value
    if node.kind == "unary" and node.children:
        if node.value == "-":
            return f"negative {_describe_node(node.children[0])}"
        return f"{node.value} {_describe_node(node.children[0])}"
    if node.kind == "binary" and len(node.children) == 2:
        return _describe_binary(node)
    if node.kind == "call":
        return _describe_call(node)
    return node.value


def _describe_call(node: ExpressionNode) -> str:
    args = list(node.children)
    if node.value == "rank" and len(args) >= 1:
        return f"cross-sectional rank of {_describe_node(args[0])}"
    if node.value == "ts_rank" and len(args) >= 2:
        return f"time-series rank of {_describe_node(args[0])} over the past {_literal_text(args[1])} days"
    if node.value == "ts_zscore" and len(args) >= 2:
        return f"{_literal_text(args[1])}-day time-series z-score of {_describe_node(args[0])}"
    if node.value == "zscore" and len(args) >= 1:
        return f"cross-sectional z-score of {_describe_node(args[0])}"
    if node.value == "ts_delta" and len(args) >= 2:
        return f"{_literal_text(args[1])}-day change in {_describe_node(args[0])}"
    if node.value == "ts_backfill" and len(args) >= 2:
        return f"backfilled {_describe_node(args[0])} using up to {_literal_text(args[1])} days of history"
    if node.value == "ts_decay_linear" and len(args) >= 2:
        return f"linearly smoothed {_describe_node(args[0])} over {_literal_text(args[1])} days"
    if node.value == "ts_mean" and len(args) >= 2:
        return f"{_literal_text(args[1])}-day average of {_describe_node(args[0])}"
    if node.value == "ts_std_dev" and len(args) >= 2:
        return f"{_literal_text(args[1])}-day standard deviation of {_describe_node(args[0])}"
    if node.value == "reverse" and len(args) >= 1:
        return f"inverted {_describe_node(args[0])}"
    if node.value == "abs" and len(args) >= 1:
        return f"absolute value of {_describe_node(args[0])}"
    if node.value == "vec_avg" and len(args) >= 1:
        return f"average vector value of {_describe_node(args[0])}"
    if node.value == "add" and args:
        return f"sum of {_join_phrases(_describe_node(arg) for arg in args)}"
    if node.value == "subtract" and len(args) >= 2:
        return f"difference between {_describe_node(args[0])} and {_describe_node(args[1])}"
    if node.value == "divide" and len(args) >= 2:
        return f"ratio of {_describe_node(args[0])} to {_describe_node(args[1])}"
    if node.value == "multiply" and len(args) >= 2:
        return f"product of {_describe_node(args[0])} and {_describe_node(args[1])}"
    return f"{node.value} applied to {_join_phrases(_describe_node(arg) for arg in args)}"


def _describe_binary(node: ExpressionNode) -> str:
    left = _describe_node(node.children[0])
    right = _describe_node(node.children[1])
    if node.value == "+":
        return f"sum of {left} and {right}"
    if node.value == "-":
        return f"difference between {left} and {right}"
    if node.value == "*":
        return f"product of {left} and {right}"
    if node.value == "/":
        return f"ratio of {left} to {right}"
    if node.value == "^":
        return f"{left} raised to the power of {right}"
    return f"{left} {node.value} {right}"


def _literal_text(node: ExpressionNode) -> str:
    if node.kind == "number":
        return node.value
    return _describe_node(node)


def _collect_fields(node: ExpressionNode) -> list[str]:
    fields = list(dict.fromkeys(_walk_field_names(node)))
    return fields


def _walk_field_names(node: ExpressionNode):
    if node.kind == "name":
        yield node.value
    for child in node.children:
        yield from _walk_field_names(child)


def _collect_functions(node: ExpressionNode) -> list[str]:
    functions = list(dict.fromkeys(_walk_functions(node)))
    return functions


def _walk_functions(node: ExpressionNode):
    if node.kind == "call":
        yield node.value
    for child in node.children:
        yield from _walk_functions(child)


def _join_phrases(phrases) -> str:
    items = [phrase for phrase in phrases if phrase]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"