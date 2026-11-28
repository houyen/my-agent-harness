#!/usr/bin/env python3
"""Quét red-team một thư mục skill (hoặc nhiều) tìm nội dung ẩn hoặc nguy hiểm. Chỉ đọc, không chạy gì.

  skill-redteam.py [--json] [--fail-on high|medium|info] [--allow RULE:chuỗi-đường-dẫn ...] DIR [DIR ...]

Ngoại lệ có kiểm soát: --allow-file redteam-allow.txt (file nằm ngoài thư mục bị quét, review cùng commit).

DIR là một skill (có SKILL.md) hoặc thư mục chứa nhiều skill. Mã thoát 1 nếu có phát hiện từ mức --fail-on
(mặc định high). Đây là lưới lọc nông bằng mẫu: sạch KHÔNG chứng minh an toàn; vẫn phải đọc tay file có script.
Chỉ dùng thư viện chuẩn.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

LEVELS = {"info": 0, "medium": 1, "high": 2}
TEXT_EXT = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".sh", ".js", ".cjs", ".mjs", ".ts", ".html", ".css", ".cmd", ""}
BINARY_EXT = {".zip", ".gz", ".tgz", ".tar", ".whl", ".exe", ".dll", ".so", ".dylib", ".pyc", ".jar", ".bin", ".7z", ".dmg"}
MAX_TEXT = 512 * 1024

INJECTION = [
    r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"disregard (all |any )?(the )?(previous|prior|above|earlier|your)",
    r"(do not|don't|never) (tell|mention|reveal|inform|show|disclose)[^.\n]{0,40}\b(the )?user",
    r"without (telling|informing|notifying|alerting) the user",
    r"\bnew (system )?instructions?\b\s*:",
    r"you are now\b",
    r"(reveal|print|output|repeat|leak)[^.\n]{0,30}(system prompt|hidden instructions)",
    r"bỏ qua (mọi|các|toàn bộ|tất cả)[^.\n]{0,20}(chỉ dẫn|hướng dẫn|quy tắc|lệnh)",
    r"(đừng|không được|không)[^.\n]{0,15}(nói|báo|cho|tiết lộ)[^.\n]{0,20}(người dùng|user)",
]
DANGER = [
    ("high", "pipe-to-shell", r"(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b"),
    ("high", "decode-and-run", r"base64\s+(-d|--decode)[^\n]*\|\s*(ba|z)?sh\b|eval\s*\(\s*(atob|base64|compile)"),
    ("high", "secret-path", r"(~|\$HOME|/Users/[^/\s]+|/home/[^/\s]+)/\.(ssh|aws|gnupg|kube|config/gcloud|netrc|docker/config\.json)|\bid_(rsa|ed25519)\b|security find-(generic|internet)-password|\b(cat|source|cp|scp|less|head|tail|grep|open|read|upload|curl[^\n]*@|base64)\s+[^\n|;]*\.env\b(?!\.example)"),
    ("high", "persistence", r"\bcrontab\b|\blaunchctl\b\s+(load|bootstrap|submit)|\bsystemctl\s+enable\b|/Library/LaunchAgents|\.bashrc|\.zshrc|\.zprofile"),
    ("high", "reverse-shell", r"/dev/tcp/|\bnc\s+(-e|-c)\b|bash\s+-i\s*>&|socat\s+[^\n]*exec"),
    ("medium", "dynamic-exec", r"\b(eval|exec)\s*\(|os\.system\s*\(|subprocess\.(run|Popen|call|check_output)|child_process|\bFunction\s*\("),
    ("medium", "network-call", r"\brequests\.(get|post|put)|urllib\.request|urlopen\(|\bsocket\.|\bfetch\s*\(|https?\.request|\bcurl\s+-|\bwget\s"),
    ("medium", "destructive", r"\brm\s+-[a-z]*r[a-z]*f?\s+(/|~|\$HOME)|\bsudo\b|\bchmod\s+(-R\s+)?[0-7]*7[0-7]*\b|\bmkfs\b|\bdd\s+if="),
    ("medium", "git-bypass", r"--no-verify|git\s+push\s+(-f|--force)|git\s+reset\s+--hard"),
]
URL = re.compile(r"https?://[^\s)>\"'`]+")
B64 = re.compile(r"[A-Za-z0-9+/]{80,}={0,2}")
HEX = re.compile(r"\b[0-9a-fA-F]{64,}\b")
HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)


def add(out, level, rule, path, line, detail):
    out.append({"level": level, "rule": rule, "file": str(path), "line": line, "detail": detail[:160]})


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def scan_text(path, rel, text, out):
    for i, ch in enumerate(text):
        cat = unicodedata.category(ch)
        if cat in ("Cf", "Co") or (cat == "Cc" and ch not in "\n\r\t"):
            add(out, "high", "invisible-char", rel, line_of(text, i), f"U+{ord(ch):04X} ({unicodedata.name(ch, 'unnamed')})")
            break
    for m in HTML_COMMENT.finditer(text):
        add(out, "medium", "html-comment", rel, line_of(text, m.start()), m.group(1).strip().replace("\n", " "))
    low = text.lower()
    for pat in INJECTION:
        for m in re.finditer(pat, low):
            add(out, "high", "injection-phrase", rel, line_of(text, m.start()), m.group(0))
    for level, rule, pat in DANGER:
        for m in re.finditer(pat, text):
            add(out, level, rule, rel, line_of(text, m.start()), m.group(0))
    for m in B64.finditer(text):
        add(out, "medium", "base64-blob", rel, line_of(text, m.start()), f"{len(m.group(0))} ký tự")
    for m in HEX.finditer(text):
        add(out, "info", "hex-blob", rel, line_of(text, m.start()), f"{len(m.group(0))} ký tự")
    for host in sorted({re.sub(r"^https?://([^/:]+).*", r"\1", u) for u in URL.findall(text)}):
        add(out, "info", "url-host", rel, 0, host)
    if rel.name == "SKILL.md":
        fm = re.match(r"---\n(.*?)\n---", text, re.S)
        if fm:
            if re.search(r"^allowed-tools:.*(Bash\(\*\)|\*\))", fm.group(1), re.M):
                add(out, "medium", "broad-allowed-tools", rel, 1, "allowed-tools rộng")
            if re.search(r"^hooks:", fm.group(1), re.M):
                add(out, "high", "frontmatter-hooks", rel, 1, "skill tự khai báo hook")


def scan_skill(root):
    out = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root.parent)
        if "__pycache__" in p.parts or p.name == ".DS_Store" or p.is_dir() and not p.is_symlink():
            continue
        if p.is_symlink():
            add(out, "high", "symlink", rel, 0, f"-> {p.readlink()}")
        elif p.suffix.lower() in BINARY_EXT:
            add(out, "high", "binary-file", rel, 0, f"{p.suffix} {p.stat().st_size} byte")
        else:
            raw = p.read_bytes()
            if b"\0" in raw[:4096]:
                add(out, "high", "binary-file", rel, 0, f"nhị phân {len(raw)} byte")
            elif len(raw) > MAX_TEXT:
                add(out, "medium", "large-file", rel, 0, f"{len(raw)} byte")
            else:
                scan_text(p, rel, raw.decode("utf-8", errors="replace"), out)
                if p.suffix.lower() not in TEXT_EXT:
                    add(out, "medium", "odd-extension", rel, 0, p.suffix)
    return out


def targets(paths):
    for d in paths:
        d = Path(d)
        if (d / "SKILL.md").is_file():
            yield d
        else:
            yield from sorted(c for c in d.iterdir() if (c / "SKILL.md").is_file())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=list(LEVELS), default="high")
    ap.add_argument("--allow", action="append", default=[], help="RULE:chuỗi-đường-dẫn, bỏ phát hiện khớp")
    ap.add_argument("--allow-file", help="file ngoại lệ ngoài thư mục bị quét; mỗi dòng `rule chuỗi-đường-dẫn  # lý do`")
    args = ap.parse_args(argv)
    allow = [a.split(":", 1) for a in args.allow if ":" in a]
    # Ngoại lệ chỉ đọc từ --allow-file do người chạy chỉ định (nằm NGOÀI thư mục bị quét). Không bao giờ dò file
    # ngoại lệ bên trong skill: skill lạ không được tự khai ngoại lệ để giấu phát hiện của chính nó.
    if args.allow_file:
        for ln in Path(args.allow_file).read_text(encoding="utf-8").splitlines():
            parts = ln.split("#", 1)[0].strip().split(None, 1)
            if len(parts) == 2:
                allow.append((parts[0], parts[1]))
    found, worst = [], -1
    for skill in targets(args.dirs):
        for f in scan_skill(skill):
            if any(f["rule"] == r and s in f["file"] for r, s in allow):
                continue
            f["skill"] = skill.name
            found.append(f)
            worst = max(worst, LEVELS[f["level"]])
    if args.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
    else:
        order = {"high": 0, "medium": 1, "info": 2}
        for f in sorted(found, key=lambda f: (order[f["level"]], f["skill"], f["file"], f["line"])):
            print(f"[{f['level']:6}] {f['rule']:18} {f['file']}:{f['line']}  {f['detail']}")
        counts = {k: sum(f["level"] == k for f in found) for k in LEVELS}
        print(f"\nTỔNG: high {counts['high']} · medium {counts['medium']} · info {counts['info']}")
    return 1 if worst >= LEVELS[args.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main())
