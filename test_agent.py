import re

from agent import calculate, execute_tool, load_history, save_history


# =========================
# calculate()
# =========================

def test_calculate_multiplication():
    assert calculate("125 * 8") == "1000"


def test_calculate_division_by_zero():
    assert calculate("10 / 0") == "Error: division by zero."


def test_calculate_rejects_injection():
    assert calculate("__import__('os').system('ls')") == "Could not calculate the expression."


# =========================
# execute_tool()
# =========================

def test_execute_tool_get_time():
    result = execute_tool("get_time", {})
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", result)


def test_execute_tool_calculate():
    assert execute_tool("calculate", {"expression": "2 + 2"}) == "4"


def test_execute_tool_unknown():
    assert execute_tool("nonexistent_tool", {}) == "Unknown tool: nonexistent_tool"


# =========================
# load_history() / save_history()
# =========================

def test_history_round_trip(tmp_path):
    path = tmp_path / "history.json"
    messages = [
        {"role": "user", "content": "Nama saya Zani"},
        {"role": "assistant", "content": "Halo Zani!"},
    ]

    save_history(path, messages)

    assert load_history(path) == messages


def test_load_history_missing_file(tmp_path):
    path = tmp_path / "does_not_exist.json"

    assert load_history(path) == []


def test_load_history_corrupt_file(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("not valid json {{{")

    assert load_history(path) == []
