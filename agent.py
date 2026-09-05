import ast
import operator
from datetime import datetime
from ollama import chat


MODEL = "qwen3:8b"


# =========================
# TOOLS
# =========================

def get_time():
    """Return the current local time."""
    return datetime.now().strftime("%H:%M:%S")


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))

    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))

    raise ValueError("Unsupported expression")


def calculate(expression):
    """Safe calculator for basic arithmetic, parsed via ast (no eval)."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree.body))
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception:
        return "Could not calculate the expression."


# =========================
# TOOL REGISTRY
# =========================

TOOL_REGISTRY = {
    "get_time": {
        "function": get_time,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Get the current local time.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        },
    },
    "calculate": {
        "function": calculate,
        "schema": {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Calculate a basic mathematical expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "A basic arithmetic expression such as 125 * 8.",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },
    },
}

tools = [entry["schema"] for entry in TOOL_REGISTRY.values()]


# =========================
# TOOL EXECUTOR
# =========================

def execute_tool(name, arguments):
    entry = TOOL_REGISTRY.get(name)

    if entry is None:
        return f"Unknown tool: {name}"

    return entry["function"](**arguments)


# =========================
# AGENT
# =========================

def run_agent(user_input):
    messages = [
        {
            "role": "user",
            "content": user_input,
        }
    ]

    while True:
        response = chat(
            model=MODEL,
            messages=messages,
            tools=tools,
        )

        messages.append(response.message)

        if not response.message.tool_calls:
            return response.message.content

        for tool_call in response.message.tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"[Tool] {name}({arguments})")

            result = execute_tool(name, arguments)

            print(f"[Result] {result}")

            messages.append(
                {
                    "role": "tool",
                    "tool_name": name,
                    "content": result,
                }
            )


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    print("ZANI AI — AGENT v0.1")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        answer = run_agent(user_input)

        print(f"AI: {answer}\n")
