"""Vỏ Claude Code cho thanh usage: `statusLine` gọi file này, payload JSON qua stdin, in 2 dòng.

Mỗi lần payload có current_usage MỚI (khác lần trước) được tính là một request. Chi phí lấy từ
payload (Claude Code tự tính), nên không cần bảng giá. Payload hỏng / thiếu → in "usage: –", exit 0.
Vẫn chuyển payload cho hook statusline của Orca nếu có (~/.orca/agent-hooks/claude-statusline.sh).
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core  # noqa: E402

ORCA_HOOK = os.path.expanduser("~/.orca/agent-hooks/claude-statusline.sh")


def chain_orca(raw):
    if os.path.isfile(ORCA_HOOK) and os.access(ORCA_HOOK, os.X_OK):
        try:
            subprocess.run(["/bin/sh", ORCA_HOOK], input=raw, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=5, check=False)
        except (OSError, subprocess.SubprocessError):
            pass  # hook Orca hỏng không được làm hỏng thanh usage


def state_path(session_id):
    sid = "".join(c for c in str(session_id or "x") if c.isalnum() or c in "-_")[:80]
    base = os.environ.get("AGENT_USAGE_STATE_DIR") or tempfile.gettempdir()
    return os.path.join(base, f"agent-usage-claude-{sid}.json")


def load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f)
        if isinstance(s, dict) and "session" in s:
            return s
    except (OSError, ValueError):
        pass
    return {"last": None, "session": core.new_usage(), "cost_last": None, "turn_cost": 0.0}


def save_state(path, s):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f)
    except OSError:
        pass  # không lưu được thì lần sau đếm lại từ đầu, thanh vẫn hiện


def line_for(payload):
    cu = (payload.get("context_window") or {}).get("current_usage")
    if not isinstance(cu, dict):
        return "usage: –"
    inp = int(cu.get("input_tokens") or 0)
    write = int(cu.get("cache_creation_input_tokens") or 0)
    read = int(cu.get("cache_read_input_tokens") or 0)
    out = int(cu.get("output_tokens") or 0)
    tokens = inp + write + read
    cost = float((payload.get("cost") or {}).get("total_cost_usd") or 0)

    path = state_path(payload.get("session_id"))
    s = load_state(path)
    cur = [inp, write, read, out]
    if s["last"] != cur:
        s["last"] = cur
        core.add(s["session"], tokens, read, write, out, 0.0)
        s["turn_cost"] = cost - s["cost_last"] if s["cost_last"] is not None else cost
        s["cost_last"] = cost
        save_state(path, s)

    turn = core.add(core.new_usage(), tokens, read, write, out, s["turn_cost"])
    pct = (payload.get("context_window") or {}).get("used_percentage")
    model = (payload.get("model") or {}).get("display_name") or ""
    return core.render(model, pct, turn, cost, 0, s["session"], turn_cost=s["turn_cost"])


def main():
    raw = sys.stdin.buffer.read()
    chain_orca(raw)
    try:
        payload = json.loads(raw or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("payload không phải object")
        print(line_for(payload))
    except (ValueError, TypeError):
        print("usage: –")


if __name__ == "__main__":
    main()
