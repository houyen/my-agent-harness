"""Lõi thanh usage dùng chung cho Claude Code và Codex: tính toán + định dạng, không I/O agent.

Hai vỏ (claude.py, codex_mcp.py) đổ số liệu vào cùng một khuôn để hai thanh đọc như nhau:
  dòng 1: <model> · ctx N% · lượt: X in / Y out · + $c · tổng $t
  dòng 2: cache: read R · write W · new N · hit H% · K req | phiên: Q req, P% từ cache
Chỉ dùng thư viện chuẩn: thanh trạng thái không được hỏng vì thiếu gói.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RATES_PATH = os.path.join(HERE, "rates.json")


def new_usage():
    return {"tokens": 0, "read": 0, "write": 0, "output": 0, "requests": 0, "cost": 0.0, "unpriced": 0}


def add(acc, tokens, read, write, output, cost):
    """Cộng một request vào acc. tokens = tổng input (đã gồm read + write). cost None = chưa có giá."""
    acc["tokens"] += tokens
    acc["read"] += read
    acc["write"] += write
    acc["output"] += output
    acc["requests"] += 1
    if cost is None:
        acc["unpriced"] += 1
    else:
        acc["cost"] += cost
    return acc


def load_rates(path=RATES_PATH):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"models": {}}


def request_cost(rates, model, tokens, read, write, output):
    """USD cho một request; None khi model chưa có giá. Bảng giá: USD / 1M token."""
    row = (rates.get("models") or {}).get(model or "")
    if not row:
        return None
    rin, rread, rwrite, rout = (row.get(k, 0) for k in ("input", "cache_read", "cache_write", "output"))
    lc = rates.get("long_context") or {}
    if lc and tokens > lc.get("threshold", float("inf")):
        m_in, m_out = lc.get("input_mult", 1), lc.get("output_mult", 1)
        rin, rread, rwrite, rout = rin * m_in, rread * m_in, rwrite * m_in, rout * m_out
    new = max(0, tokens - read - write)
    return (new * rin + read * rread + write * rwrite + output * rout) / 1_000_000


def compact(n):
    n = n or 0
    for unit, div in (("M", 1_000_000), ("k", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(int(n))


def cost_label(cost, unpriced=0):
    if unpriced:
        return f"${cost:.4f} + ? ({unpriced} req chưa có giá)" if cost else "chưa có giá"
    return f"${cost:.4f}"


def render(model, ctx_pct, turn, total_cost, total_unpriced, session, turn_cost=None):
    """Hai dòng. turn = usage lượt hiện tại (None = chưa có), session = usage cả phiên.

    turn_cost: chi phí lượt khi agent tự báo (Claude); None thì lấy turn["cost"].
    """
    head = [model or "agent"]
    if ctx_pct is not None:
        head.append(f"ctx {ctx_pct:.0f}%")
    if not turn or not turn.get("requests"):
        return " · ".join(head + ["lượt: chờ dữ liệu"])
    tc = turn["cost"] if turn_cost is None else turn_cost
    tu = turn["unpriced"] if turn_cost is None else 0
    head += [
        f"lượt: {compact(turn['tokens'])} in / {compact(turn['output'])} out",
        "+ " + cost_label(tc, tu),
        "tổng " + cost_label(total_cost, total_unpriced),
    ]
    new = max(0, turn["tokens"] - turn["read"] - turn["write"])
    cache = f"cache: read {compact(turn['read'])} · write {compact(turn['write'])} · new {compact(new)}"
    if turn["tokens"]:
        cache += f" · hit {turn['read'] / turn['tokens']:.0%}"
    cache += f" · {turn['requests']} req"
    if session and session.get("requests"):
        share = session["read"] / session["tokens"] if session["tokens"] else 0
        cache += f" | phiên: {session['requests']} req, {share:.0%} từ cache"
    return " · ".join(head) + "\n" + cache
