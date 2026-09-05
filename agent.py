import ast
import json
import operator
import urllib.error
import urllib.parse
import urllib.request
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


COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
HTTP_TIMEOUT = 10

# Common ticker symbols -> CoinGecko coin ids. Anything not listed here is passed
# straight through as an id (lowercased), so full names like "bitcoin" work too.
_COIN_ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "dot": "polkadot",
    "matic": "matic-network",
    "ltc": "litecoin",
    "trx": "tron",
    "avax": "avalanche-2",
    "link": "chainlink",
    "usdt": "tether",
    "usdc": "usd-coin",
    "shib": "shiba-inu",
}


def _get_json(url):
    """Fetch a URL and parse its JSON body. Isolated so tests can stub the network."""
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent/0.1"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
        return json.load(response)


def get_crypto_price(coin):
    """Get a cryptocurrency's current USD price and 24h change from CoinGecko."""
    key = coin.strip().lower()

    if not key:
        return "Please provide a coin name or symbol, e.g. 'bitcoin' or 'btc'."

    coin_id = _COIN_ALIASES.get(key, key)

    query = urllib.parse.urlencode(
        {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        }
    )

    try:
        data = _get_json(f"{COINGECKO_PRICE_URL}?{query}")
    except urllib.error.HTTPError as e:
        return f"CoinGecko API error (HTTP {e.code}). Try again in a moment."
    except (urllib.error.URLError, TimeoutError):
        return "Could not reach the CoinGecko API. Check your connection and try again."
    except (json.JSONDecodeError, ValueError):
        return "Got an unexpected response from the CoinGecko API."

    entry = data.get(coin_id)

    if not entry or "usd" not in entry:
        return (
            f"Cryptocurrency '{coin}' not found. "
            "Use the full name (e.g. 'bitcoin') or a common symbol (e.g. 'btc')."
        )

    price = entry["usd"]
    change = entry.get("usd_24h_change")

    price_str = f"${price:,.2f}" if price >= 1 else f"${price:,.8f}"
    change_str = "24h change: n/a" if change is None else f"24h change: {change:+.2f}%"

    return f"{coin_id.replace('-', ' ').title()}: {price_str} USD ({change_str})"


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
    "get_crypto_price": {
        "function": get_crypto_price,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_crypto_price",
                "description": (
                    "Get the current USD price and 24-hour change of a "
                    "cryptocurrency (e.g. Bitcoin, Ethereum) from CoinGecko."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin": {
                            "type": "string",
                            "description": (
                                "Cryptocurrency name or ticker symbol, "
                                "e.g. 'bitcoin', 'ethereum', 'btc', 'eth'."
                            ),
                        }
                    },
                    "required": ["coin"],
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
