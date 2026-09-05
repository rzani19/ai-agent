import ast
import json
import operator
from datetime import datetime
from pathlib import Path

from ollama import ResponseError, chat


MODEL = "qwen3:8b"
PROJECT_ROOT = Path(__file__).parent.resolve()
HISTORY_FILE = PROJECT_ROOT / "conversation_history.json"
MAX_READ_CHARS = 5000


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


def read_file(path, root=PROJECT_ROOT):
    """Read a text file's content, restricted to files inside `root`."""
    root = Path(root).resolve()

    try:
        target = (root / path).resolve()
    except OSError:
        return "Invalid path."

    if not target.is_relative_to(root):
        return "Access denied: path is outside the project folder."

    if not target.exists():
        return f"File not found: {path}"

    if not target.is_file():
        return f"Not a file: {path}"

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "Could not read file: not a valid text file."
    except OSError as e:
        return f"Could not read file: {e}"

    if len(content) > MAX_READ_CHARS:
        return content[:MAX_READ_CHARS] + f"\n... (truncated, showing first {MAX_READ_CHARS} characters)"

    return content


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
    "read_file": {
        "function": read_file,
        "schema": {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the content of a text file inside the project folder (max 5000 characters).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file, relative to the project folder.",
                        }
                    },
                    "required": ["path"],
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

    try:
        return entry["function"](**arguments)
    except TypeError as e:
        return f"Tool '{name}' was called with invalid arguments: {e}"


# =========================
# CONVERSATION HISTORY
# =========================

def load_history(path):
    if not Path(path).exists():
        return []

    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"[Warning] Could not read history file at {path}, starting fresh.")
        return []


def save_history(path, messages):
    path = Path(path)
    tmp_path = path.with_suffix(".json.tmp")

    with open(tmp_path, "w") as f:
        json.dump(messages, f, indent=2)

    tmp_path.replace(path)


# =========================
# AGENT
# =========================

def run_agent(user_input, messages):
    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    while True:
        try:
            response = chat(
                model=MODEL,
                messages=messages,
                tools=tools,
            )
        except ConnectionError:
            return (
                "Error: could not connect to Ollama. "
                "Make sure it's running (`ollama serve`) and try again."
            )
        except ResponseError as e:
            if e.status_code == 404:
                return f"Error: model '{MODEL}' not found. Pull it first with `ollama pull {MODEL}`."
            return f"Error: Ollama returned an error: {e.error}"

        messages.append(response.message.model_dump())

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

    messages = load_history(HISTORY_FILE)

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        try:
            answer = run_agent(user_input, messages)
        except Exception as e:
            print(f"[Error] Unexpected error: {e}\n")
            continue

        save_history(HISTORY_FILE, messages)

        print(f"AI: {answer}\n")
