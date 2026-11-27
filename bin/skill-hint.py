#!/usr/bin/env python3
"""Hook UserPromptSubmit: gợi ý skill hợp với câu user vừa gõ. Chỉ gợi ý, không chạy skill, không chặn.

Đọc JSON hook từ stdin (khoá `prompt`, `session_id`), so với profiles/personal/skill-hints.json
(đổi đường dẫn bằng SKILL_HINTS_FILE). In tối đa 2 dòng gợi ý ra stdout (vào ngữ cảnh model).
Luôn thoát 0; lỗi bất kỳ thì im lặng. Tắt hẳn bằng SKILL_HINT_OFF=1.
Không ghi nội dung prompt vào log, chỉ tên skill và cụm khớp.
"""
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAX_HINTS = 2
MIN_LEN = 8
COOLDOWN = 3  # không gợi lại cùng skill trong 3 prompt kế


def fold(text):
    """Chữ thường, bỏ dấu tiếng Việt, đ -> d."""
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def match(prompt, hints):
    text = fold(prompt)
    found = []
    for name, spec in hints.items():
        if name.startswith("_") or not isinstance(spec, dict):
            continue
        hit = [p for p in spec.get("phrases", []) if re.search(r"(?<![a-z0-9])" + re.escape(fold(p)) + r"(?![a-z0-9])", text)]
        if hit:
            found.append((len(hit), name, hit[0]))
    found.sort(key=lambda r: (-r[0], r[1]))
    return found


def state_path():
    return Path(os.environ.get("SKILL_HINT_STATE") or (Path(os.environ.get("HOME", "/tmp")) / ".claude/.skill-hint-state.json"))


def main():
    if os.environ.get("SKILL_HINT_OFF") == "1":
        return
    data = json.loads(sys.stdin.read() or "{}")
    prompt = (data.get("prompt") or "").strip()
    if len(prompt) < MIN_LEN or prompt.startswith("/"):
        return
    hints_file = Path(os.environ.get("SKILL_HINTS_FILE") or REPO / "profiles/personal/skill-hints.json")
    hints = json.loads(hints_file.read_text(encoding="utf-8"))
    found = match(prompt, hints)
    if not found:
        return
    sid = str(data.get("session_id") or "none")
    sp = state_path()
    try:
        state = json.loads(sp.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    sess = state.get(sid) or {"n": 0, "last": {}}
    sess["n"] += 1
    lines, shown = [], []
    for _, name, phrase in found:
        if sess["n"] - sess["last"].get(name, -99) <= COOLDOWN:
            continue
        spec = hints[name]
        lines.append(f"- {spec.get('invoke', '/' + name)}: {spec.get('why', '')}")
        shown.append((name, phrase))
        sess["last"][name] = sess["n"]
        if len(shown) == MAX_HINTS:
            break
    state[sid] = sess
    if len(state) > 20:
        for k in sorted(state, key=lambda k: state[k]["n"])[: len(state) - 20]:
            del state[k]
    try:
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass
    if not shown:
        return
    print("[skill-hint] Skill có thể hợp với yêu cầu này (chỉ gợi ý; nhắc user ngắn gọn nếu thật sự hợp, đừng tự chạy skill gọi-tay):")
    print("\n".join(lines))
    log = Path(os.environ.get("HOME", "/tmp")) / ".claude/skill-hint.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            for name, phrase in shown:
                fh.write(json.dumps({"ts": int(time.time()), "skill": name, "phrase": phrase}, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
