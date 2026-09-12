"""
Tools: Safe Calculator Execution Tool.

Evaluates mathematical expressions deterministically. Instrumented with tracing
and fault injection hooks.
"""

import ast
import operator
from typing import Dict, Any, Optional
from observability.tracing import global_tracer
from observability.metrics import global_metrics
from chaos.tool_faults import ToolFaultInjector

# Safe operator mapping to avoid unsafe eval()
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_ast(node):
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported math operator: {type(node.op)}")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast(node.operand)
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        return op(operand)
    else:
        raise ValueError(f"Unsupported expression element: {type(node)}")


def calculate(expression: str, fault_injector: Optional[ToolFaultInjector] = None) -> Dict[str, Any]:
    """
    Safely evaluate a mathematical expression.
    """
    with global_tracer.span("tool:calculator", {"expression": expression}) as span:
        global_metrics.record_tool_call()

        if fault_injector:
            fault_override = fault_injector.intercept("calculator", {"expression": expression}, lambda **kwargs: calculate(**kwargs))
            if fault_override is not None:
                span.set_attribute("fault_injected", True)
                return {"result": fault_override}

        try:
            tree = ast.parse(expression, mode="eval")
            result = _eval_ast(tree.body)
            return {"status": "SUCCESS", "expression": expression, "result": result}
        except Exception as exc:
            span.set_attribute("error", str(exc))
            return {"status": "ERROR", "expression": expression, "error": str(exc)}
