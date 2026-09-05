import re

from ollama import ResponseError

import agent
from agent import calculate, execute_tool, load_history, read_file, run_agent, save_history


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


def test_execute_tool_missing_argument():
    result = execute_tool("calculate", {})

    assert "invalid arguments" in result.lower()


def test_execute_tool_unexpected_argument():
    result = execute_tool("get_time", {"unexpected": "value"})

    assert "invalid arguments" in result.lower()


# =========================
# run_agent() error handling
# =========================

def test_run_agent_connection_error(monkeypatch):
    def fake_chat(*args, **kwargs):
        raise ConnectionError("Failed to connect to Ollama.")

    monkeypatch.setattr(agent, "chat", fake_chat)

    result = run_agent("hi", [])

    assert "could not connect" in result.lower()


def test_run_agent_model_not_found(monkeypatch):
    def fake_chat(*args, **kwargs):
        raise ResponseError("model 'qwen3:8b' not found, try pulling it first", 404)

    monkeypatch.setattr(agent, "chat", fake_chat)

    result = run_agent("hi", [])

    assert "not found" in result.lower()
    assert "ollama pull" in result.lower()


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


# =========================
# read_file()
# =========================

def test_read_file_existing(tmp_path):
    (tmp_path / "note.txt").write_text("hello world")

    assert read_file("note.txt", root=tmp_path) == "hello world"


def test_read_file_missing(tmp_path):
    assert read_file("missing.txt", root=tmp_path) == "File not found: missing.txt"


def test_read_file_rejects_path_traversal(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")

    result = read_file("../secret.txt", root=project_dir)

    assert result == "Access denied: path is outside the project folder."


def test_read_file_truncates_long_content(tmp_path):
    (tmp_path / "big.txt").write_text("x" * 6000)

    result = read_file("big.txt", root=tmp_path)

    assert result.startswith("x" * 5000)
    assert "truncated" in result
