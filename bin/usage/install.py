"""Cài / gỡ thanh usage cho Claude Code và Codex (GLOBAL, của máy, không theo repo).

  python3 bin/usage/install.py install [--replace] [--only claude|codex]
  python3 bin/usage/install.py uninstall
  python3 bin/usage/install.py status

- Chép core.py, claude.py, codex_mcp.py, rates.json vào ~/.agent-usage/ (AGENT_USAGE_HOME để đổi).
- Claude: `statusLine` trong ~/.claude/settings.json.
- Codex: khối có đánh dấu `[mcp_servers.agent-usage]` + dòng `status_line_provider` trong [tui]
  của $CODEX_HOME/config.toml. Kiểm cú pháp bằng tomllib trước khi ghi; sai thì không ghi.
- Đã có statusLine / status_line_provider KHÁC → giữ nguyên và báo; --replace mới thay, giá trị cũ
  cất ở ~/.agent-usage/previous.json để uninstall trả lại. Chạy lại nhiều lần cho cùng kết quả.
Mã thoát: 0 = ổn; 1 = lỗi (cấu hình hỏng, ghi không được).
"""

import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path

SRC = Path(__file__).resolve().parent
FILES = ("core.py", "claude.py", "codex_mcp.py", "rates.json")
SERVER = "agent-usage"
BEGIN = "# >>> agent-usage (my-agent-harness) >>>"
END = "# <<< agent-usage <<<"
TAG = "# agent-usage"
PY = sys.executable or "python3"


def home():
    return Path(os.environ.get("AGENT_USAGE_HOME") or Path.home() / ".agent-usage")


def claude_settings():
    return Path.home() / ".claude" / "settings.json"


def codex_config():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "config.toml"


def log(msg):
    print(f"[agent-usage] {msg}")


def load_prev():
    try:
        return json.loads((home() / "previous.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_prev(prev):
    (home() / "previous.json").write_text(json.dumps(prev, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Claude ────────────────────────────────────────────────────────────────

def ours_claude(sl):
    if not isinstance(sl, dict):
        return False
    cmd = str(sl.get("command", ""))
    return str(home() / "claude.py") in cmd or "/.agent-usage/claude.py" in cmd


def read_json(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))  # hỏng → ValueError, để main báo lỗi
    if not isinstance(data, dict):
        raise ValueError(f"{path} không phải JSON object")
    return data


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def install_claude(replace, prev):
    path = claude_settings()
    data = read_json(path)
    want = {"type": "command", "command": f'"{PY}" "{home() / "claude.py"}"'}
    cur = data.get("statusLine")
    if cur == want:
        log("Claude: statusLine đã trỏ agent-usage — không đổi")
        return
    if cur and not ours_claude(cur):
        if not replace:
            log(f"Claude: đã có statusLine khác ({cur.get('command', cur)}) — GIỮ NGUYÊN; chạy lại với --replace để thay")
            return
        prev.setdefault("claude_statusLine", cur)
    data["statusLine"] = want
    write_json(path, data)
    log(f"Claude: statusLine → {want['command']}")


def uninstall_claude(prev):
    path = claude_settings()
    data = read_json(path)
    if not ours_claude(data.get("statusLine")):
        log("Claude: statusLine không phải của agent-usage — bỏ qua")
        return
    if "claude_statusLine" in prev:
        data["statusLine"] = prev.pop("claude_statusLine")
        log("Claude: trả lại statusLine cũ")
    else:
        data.pop("statusLine", None)
        log("Claude: gỡ statusLine")
    write_json(path, data)


# ── Codex ─────────────────────────────────────────────────────────────────

def strip_block(text):
    return re.sub(rf"\n?{re.escape(BEGIN)}.*?{re.escape(END)}\n?", "\n", text, flags=re.S)


def tui_span(lines):
    """(chỉ số dòng [tui], chỉ số dòng header kế tiếp) hoặc None."""
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "[tui]"), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    return start, end


def provider_line():
    return f'status_line_provider = {{ server = "{SERVER}", tool = "statusline" }}  {TAG}'


def mcp_block():
    return "\n".join([BEGIN, f"[mcp_servers.{SERVER}]", f'command = "{PY}"',
                      f'args = ["-u", "{home() / "codex_mcp.py"}"]', END, ""])


def write_toml(path, text):
    tomllib.loads(text)  # sai cú pháp → TOMLDecodeError, không ghi
    bak = path.with_name(path.name + ".bak-agent-usage")
    if path.exists() and not bak.exists():
        shutil.copy2(path, bak)
    tmp = path.with_suffix(".toml.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def install_codex(replace, prev):
    path = codex_config()
    path.parent.mkdir(parents=True, exist_ok=True)
    orig = path.read_text(encoding="utf-8") if path.exists() else ""
    tomllib.loads(orig)  # config hỏng sẵn → không động vào
    lines = strip_block(orig).rstrip("\n").split("\n") if orig.strip() else []
    span = tui_span(lines)
    if span is None:
        lines += ["", "[tui]", provider_line()]
    else:
        start, end = span
        idx = next((i for i in range(start + 1, end) if lines[i].lstrip().startswith("status_line_provider")), None)
        if idx is None:
            lines.insert(start + 1, provider_line())
        elif TAG in lines[idx] or f'"{SERVER}"' in lines[idx]:
            lines[idx] = provider_line()
        elif not replace:
            log(f"Codex: đã có provider khác ({lines[idx].strip()}) — GIỮ NGUYÊN; chạy lại với --replace để thay")
            return
        else:
            prev.setdefault("codex_provider_line", lines[idx])
            lines[idx] = provider_line()
    text = "\n".join(lines).rstrip("\n") + "\n\n" + mcp_block()
    if text == orig:
        log("Codex: đã cài — không đổi")
        return
    write_toml(path, text)
    log(f"Codex: [mcp_servers.{SERVER}] + tui.status_line_provider → {path}")


def uninstall_codex(prev):
    path = codex_config()
    if not path.exists():
        log("Codex: không có config.toml — bỏ qua")
        return
    orig = path.read_text(encoding="utf-8")
    lines = strip_block(orig).rstrip("\n").split("\n")
    out = []
    for ln in lines:
        if ln.lstrip().startswith("status_line_provider") and TAG in ln:
            if "codex_provider_line" in prev:
                out.append(prev.pop("codex_provider_line"))
            continue
        out.append(ln)
    text = "\n".join(out).rstrip("\n") + "\n"
    if text != orig:
        write_toml(path, text)
        log("Codex: gỡ agent-usage khỏi config.toml")
    else:
        log("Codex: không có agent-usage trong config.toml")


# ── lệnh ──────────────────────────────────────────────────────────────────

def copy_files():
    home().mkdir(parents=True, exist_ok=True)
    for f in FILES:
        shutil.copy2(SRC / f, home() / f)
    log(f"chép {', '.join(FILES)} → {home()}")


def status():
    try:
        sl = read_json(claude_settings()).get("statusLine")
    except ValueError as e:
        sl = f"lỗi đọc: {e}"
    print(f"files : {'có' if all((home() / f).exists() for f in FILES) else 'thiếu'} ({home()})")
    print(f"claude: {'agent-usage' if ours_claude(sl) else (sl or 'chưa có')}")
    cfg = codex_config()
    txt = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
    print(f"codex : {'agent-usage' if BEGIN in txt and TAG in txt else 'chưa cài'} ({cfg})")


def main(argv):
    if not argv or argv[0] not in ("install", "uninstall", "status"):
        print(__doc__.strip())
        return 1
    cmd, rest = argv[0], argv[1:]
    replace = "--replace" in rest
    only = rest[rest.index("--only") + 1] if "--only" in rest and rest.index("--only") + 1 < len(rest) else None
    if cmd == "status":
        status()
        return 0
    try:
        prev = load_prev()
        if cmd == "install":
            copy_files()
            if only in (None, "claude"):
                install_claude(replace, prev)
            if only in (None, "codex"):
                install_codex(replace, prev)
        else:
            if only in (None, "claude"):
                uninstall_claude(prev)
            if only in (None, "codex"):
                uninstall_codex(prev)
        if home().exists():
            save_prev(prev)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as e:
        print(f"[agent-usage] LỖI: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
