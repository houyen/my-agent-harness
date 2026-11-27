"""Vỏ Codex cho thanh usage: MCP server qua stdio, khai trong config.toml làm tui.status_line_provider.

Codex gửi trạng thái phiên trong `_meta["com.openai/codex-statusline-state"]` của resources/read.
Số token lấy từ log phiên ($CODEX_HOME/sessions/*/*/*/rollout-*-<thread>.jsonl), đọc nối tiếp theo
offset; chi phí tính bằng rates.json (model chưa có giá → "chưa có giá").
"""

import json
import os
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402

SERVER = "agent-usage"
URI = "ui://agent-usage/footer"
TOOL = {
    "name": "statusline",
    "title": "Agent usage",
    "description": "Show per-turn token usage and estimated API costs in the Codex footer.",
    "inputSchema": {"type": "object", "properties": {}},
    "_meta": {"openai/ui": {"entrypoints": [{"type": "statusline", "resourceUri": URI}]}},
}
MARKERS = (b'"token_usage_record"', b'"turn_context"', b'"task_started"')

RATES = core.load_rates()
history = {}


def codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def new_history(path):
    return {"path": path, "offset": 0, "responses": set(), "models": {}, "turns": {},
            "current": None, "session": core.new_usage()}


def apply_record(state, record, thread_id):
    payload = record.get("payload") or {}
    turn_id = payload.get("turn_id")
    if not turn_id:
        return
    root = payload.get("root_turn_id") or turn_id
    kind = record.get("type")
    if kind == "turn_context":
        state["models"][turn_id] = payload.get("model")
        if state["current"] is None:
            state["current"] = root
    if kind == "event_msg" and payload.get("type") == "task_started":
        state["current"] = root
    if kind != "token_usage_record" or payload.get("thread_id") != thread_id:
        return
    response, usage = payload.get("response_id"), payload.get("usage")
    if not response or not usage or response in state["responses"]:
        return
    state["responses"].add(response)
    tokens = usage.get("input_tokens", 0)
    read = usage.get("cached_input_tokens", 0)
    write = usage.get("cache_write_input_tokens", 0)
    output = usage.get("output_tokens", 0)
    model = state["models"].get(turn_id) or state["models"].get(root)
    cost = core.request_cost(RATES, model, tokens, read, write, output)
    core.add(state["turns"].setdefault(root, core.new_usage()), tokens, read, write, output, cost)
    core.add(state["session"], tokens, read, write, output, cost)


def read_log(state, thread_id):
    with state["path"].open("rb") as log:
        if log.seek(0, 2) < state["offset"]:  # log bị cắt/ghi lại → đọc lại từ đầu
            state.update(new_history(state["path"]))
        log.seek(state["offset"])
        while line := log.readline():
            if not line.endswith(b"\n"):
                break  # dòng đang ghi dở, đợi lần sau
            state["offset"] = log.tell()
            if not any(m in line for m in MARKERS):
                continue
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if isinstance(record, dict):
                apply_record(state, record, thread_id)


def thread_usage(thread_id):
    try:
        thread_id = str(UUID(thread_id))
    except (ValueError, TypeError, AttributeError):
        return None
    state = history.get(thread_id)
    if state is None:
        path = next((codex_home() / "sessions").glob(f"*/*/*/rollout-*-{thread_id}.jsonl"), None)
        if path is None:
            return None
        state = history[thread_id] = new_history(path)
    try:
        read_log(state, thread_id)
    except OSError:
        history.pop(thread_id, None)
        return None
    return state


def render(cx):
    thread = cx.get("thread") or {}
    model = thread.get("model") or {}
    name = model.get("display_name") or "Codex"
    if model.get("reasoning_level"):
        name += f" {model['reasoning_level']}"
    pct = ((thread.get("usage") or {}).get("context") or {}).get("used_percentage")
    st = thread_usage(thread.get("id", ""))
    if not st:
        return core.render(name, pct, None, 0, 0, None)
    s = st["session"]
    return core.render(name, pct, st["turns"].get(st["current"]), s["cost"], s["unpriced"], s)


def respond(method, params):
    if method == "initialize":
        return {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": SERVER, "version": "1.0"}}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call":
        if params.get("name") != TOOL["name"]:
            raise ValueError("Unknown tool name")
        return {"content": [{"type": "text", "text": f"The statusline resource is {URI}."}]}
    if method == "resources/list":
        return {"resources": [{"name": "footer", "uri": URI, "mimeType": "application/json"}]}
    if method == "resources/templates/list":
        return {"resourceTemplates": []}
    if method == "resources/read":
        if params.get("uri") != URI:
            raise ValueError("Unknown resource URI")
        cx = (params.get("_meta") or {}).get("com.openai/codex-statusline-state") or {}
        text = json.dumps(render(cx), ensure_ascii=False)
        return {"contents": [{"uri": URI, "mimeType": "application/json", "text": text}]}
    raise KeyError(method)


def main():
    for line in sys.stdin.buffer:
        reply = {"jsonrpc": "2.0", "id": None}
        try:
            req = json.loads(line)
            if not isinstance(req, dict) or not isinstance(req.get("method"), str):
                reply["error"] = {"code": -32600, "message": "Invalid request"}
            elif "id" not in req:
                continue  # notification
            else:
                reply["id"] = req["id"]
                reply["result"] = respond(req["method"], req.get("params") or {})
        except json.JSONDecodeError:
            reply["error"] = {"code": -32700, "message": "Parse error"}
        except KeyError:
            reply["error"] = {"code": -32601, "message": "Method not found"}
        except (TypeError, ValueError, AttributeError):
            reply["error"] = {"code": -32602, "message": "Invalid parameters"}
        print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
