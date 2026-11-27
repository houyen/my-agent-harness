#!/usr/bin/env python3
"""Cài và kiểm một hồ sơ Claude Code toàn cục (~/.claude) từ profiles/<tên>/.

  profile.py install [--profile personal] [--private DIR] [--dry-run] [--keep-legacy-hooks] [--force-docs] [--with-moli]
  profile.py check   [--profile personal] [--private DIR] [--json]
  profile.py context [--profile personal]

Chỉ dùng thư viện chuẩn. HOME lấy từ biến môi trường, nên test được bằng HOME tạm.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOLI_INSTALLER = "https://github.com/lexmount/moli/releases/latest/download/moli-installer.sh"
LEGACY_MARKERS = ("llmwiki/.harness-stamp", "/.claude/harness/")
DOCS = ("CLAUDE.md", "RTK.md")
HIDDEN = ("user-invocable-only", "off")


def home():
    return Path(os.environ["HOME"])


def load_profile(name):
    pdir = REPO / "profiles" / name
    if not pdir.is_dir():
        sys.exit(f"không có profile: {pdir}")
    spec = json.loads((pdir / "skills.json").read_text(encoding="utf-8"))
    settings = json.loads((pdir / "settings.json").read_text(encoding="utf-8"))
    return pdir, spec, settings


def public_skills():
    return sorted(p.name for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())


def private_dir(arg):
    raw = arg or os.environ.get("MAH_PRIVATE_DIR")
    return Path(raw).expanduser().resolve() if raw else None


def wanted_links(spec, priv):
    """Tên skill → thư mục nguồn. Thiếu repo riêng thì nguồn = None."""
    out = {n: REPO / "skills" / n for n in public_skills()}
    for n in spec.get("private", []):
        out[n] = (priv / "skills" / n) if priv else None
    return out


def legacy_hooks(settings):
    found = []
    for event, groups in (settings.get("hooks") or {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                if any(m in h.get("command", "") for m in LEGACY_MARKERS):
                    found.append(event)
    return found


def prune_legacy(settings):
    hooks = settings.get("hooks") or {}
    for event in list(hooks):
        groups = []
        for g in hooks[event]:
            g["hooks"] = [h for h in g.get("hooks", []) if not any(m in h.get("command", "") for m in LEGACY_MARKERS)]
            if g["hooks"]:
                groups.append(g)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def evaluate(profile, priv_arg):
    """Trả danh sách (mức, thông điệp). mức: error | warn | info."""
    pdir, spec, want = load_profile(profile)
    priv = private_dir(priv_arg)
    sk = home() / ".claude/skills"
    issues = []
    for name, src in wanted_links(spec, priv).items():
        dst = sk / name
        if src is None:
            issues.append(("warn", f"skill riêng {name}: chưa có --private/MAH_PRIVATE_DIR"))
        elif not (src / "SKILL.md").is_file():
            issues.append(("error", f"skill {name}: nguồn thiếu {src}"))
        elif not dst.is_symlink() or dst.resolve() != src.resolve():
            issues.append(("error", f"skill {name}: chưa link tới {src}"))
    if sk.is_dir():
        for p in sorted(sk.iterdir()):
            if p.is_symlink() and not p.exists():
                issues.append(("error", f"symlink chết: {p}"))
    for name, how in spec.get("external", {}).items():
        if not (sk / name).exists():
            issues.append(("warn", f"skill ngoài {name} chưa có (cài qua: {how})"))
    cur = read_json(home() / ".claude/settings.json")
    for key, val in want.items():
        if cur.get(key) != val:
            issues.append(("error", f"settings.json lệch khoá {key}"))
    for ev in sorted(set(legacy_hooks(cur))):
        issues.append(("error", f"hook llmwiki cũ còn ở {ev}"))
    for doc in DOCS:
        dst = home() / ".claude" / doc
        if not dst.exists():
            issues.append(("error", f"thiếu ~/.claude/{doc}"))
        elif dst.read_bytes() != (pdir / doc).read_bytes():
            issues.append(("warn", f"~/.claude/{doc} khác bản profile"))
    tools = spec.get("tools", {})
    for t in tools.get("required", []):
        if not shutil.which(t):
            issues.append(("error", f"thiếu công cụ bắt buộc: {t}"))
    for t in tools.get("optional", []):
        if not shutil.which(t):
            issues.append(("info", f"thiếu công cụ tuỳ chọn: {t}"))
    return issues


def backup(path, stamp):
    if path.exists() or path.is_symlink():
        dst = home() / ".claude/profile-backups" / stamp / path.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dst))
        return dst
    return None


def install(args):
    pdir, spec, want = load_profile(args.profile)
    priv = private_dir(args.private)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    sk = home() / ".claude/skills"
    changes = []
    for name, src in wanted_links(spec, priv).items():
        if src is None or not (src / "SKILL.md").is_file():
            print(f"  bỏ qua {name}: không có nguồn")
            continue
        dst = sk / name
        if dst.is_symlink() and dst.resolve() == src.resolve():
            continue
        changes.append(f"link {name} -> {src}")
        if not args.dry_run:
            sk.mkdir(parents=True, exist_ok=True)
            moved = backup(dst, stamp)
            if moved:
                changes.append(f"  bản cũ -> {moved}")
            dst.symlink_to(src)
    for p in sorted(sk.iterdir()) if sk.is_dir() else []:
        if p.is_symlink() and not p.exists():
            changes.append(f"gỡ symlink chết {p.name}")
            if not args.dry_run:
                p.unlink()
    sp = home() / ".claude/settings.json"
    cur = read_json(sp)
    new = json.loads(json.dumps(cur))
    new.update(want)
    if not args.keep_legacy_hooks:
        prune_legacy(new)
    if new != cur:
        parts = [k for k in want if cur.get(k) != want[k]]
        if legacy_hooks(cur) and not args.keep_legacy_hooks:
            parts.append("gỡ hook llmwiki cũ")
        changes.append("cập nhật settings.json (" + ", ".join(parts) + ")")
        if not args.dry_run:
            sp.parent.mkdir(parents=True, exist_ok=True)
            if sp.exists():
                bdir = home() / ".claude/profile-backups" / stamp
                bdir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sp, bdir / "settings.json")
            sp.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for doc in DOCS:
        dst = home() / ".claude" / doc
        src = pdir / doc
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            continue
        if dst.exists() and not args.force_docs:
            print(f"  ~/.claude/{doc} khác bản profile: giữ nguyên (--force-docs để thay, có sao lưu)")
            continue
        changes.append(f"chép {doc}")
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                backup(dst, stamp)
            shutil.copy2(src, dst)
    if args.with_moli and not shutil.which("moli"):
        changes.append(f"cài Moli từ {MOLI_INSTALLER}")
        if not args.dry_run:
            subprocess.run(f"curl --proto '=https' --tlsv1.2 -fsSL {MOLI_INSTALLER} | sh", shell=True, check=False)
    tag = "[dry-run] " if args.dry_run else ""
    print("\n".join(f"{tag}{c}" for c in changes) if changes else "không có gì thay đổi")
    rest = [m for lvl, m in evaluate(args.profile, args.private) if lvl != "error" or "thiếu công cụ" in m]
    for m in rest:
        print(f"  lưu ý: {m}")
    return 0


def check(args):
    issues = evaluate(args.profile, args.private)
    if args.json:
        print(json.dumps([{"level": lvl, "message": m} for lvl, m in issues], ensure_ascii=False, indent=2))
    else:
        for lvl, m in issues:
            print(f"[{lvl}] {m}")
        if not issues:
            print("profile khớp")
    return 1 if any(lvl == "error" for lvl, _ in issues) else 0


def frontmatter(path):
    """Đọc name/description/disable-model-invocation từ frontmatter, không cần PyYAML."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out, key, buf = {}, None, []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line[:1] not in (" ", "\t") and ":" in line:
            if key:
                out[key] = " ".join(buf).strip()
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            buf = [] if val in (">", ">-", "|", "|-") else [val.strip("'\"")]
        elif key:
            buf.append(line.strip())
    if key:
        out[key] = " ".join(buf).strip()
    return out


def estimate_tokens(text):
    # Ước lượng thô: ~3 ký tự/token cho văn bản trộn Việt-Anh. Số thật: chạy /context trong Claude Code.
    return round(len(text) / 3)


def expand_doc(path, seen=None):
    seen = seen or set()
    if path in seen or not path.is_file():
        return ""
    seen.add(path)
    parts = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("@") and " " not in line.strip():
            parts.append(expand_doc(path.parent / line[1:].strip(), seen))
        else:
            parts.append(line)
    return "\n".join(parts)


def context(args):
    pdir, spec, want = load_profile(args.profile)
    priv = private_dir(args.private)
    overrides = want.get("skillOverrides", {})
    docs = expand_doc(pdir / "CLAUDE.md")
    rows = []
    for name, src in sorted(wanted_links(spec, priv).items()):
        mode = overrides.get(name, "on")
        if src is None or not (src / "SKILL.md").is_file():
            rows.append((name, mode, None))
            continue
        fm = frontmatter(src / "SKILL.md")
        if mode in HIDDEN or fm.get("disable-model-invocation") == "true":
            text = ""
        elif mode == "name-only":
            text = name
        else:
            text = f"- {name}: {fm.get('description', '')}"
        rows.append((name, mode, estimate_tokens(text)))
    shown = [r for r in rows if r[2]]
    total_sk = sum(r[2] for r in shown)
    total_doc = estimate_tokens(docs)
    print(f"CLAUDE.md toàn cục (gồm @import): ~{total_doc} token")
    print(f"Mô tả skill model thấy ({len(shown)}/{len(rows)} skill): ~{total_sk} token")
    for name, mode, tok in sorted(rows, key=lambda r: -(r[2] or 0)):
        label = "không có nguồn" if tok is None else (f"~{tok}" if tok else "ẩn")
        print(f"  {name:28} {mode:20} {label}")
    print(f"Tổng phần profile nạp đầu phiên: ~{total_doc + total_sk} token "
          "(chưa gồm system prompt, skill built-in, MCP, CLAUDE.md/memory của dự án)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("install", "check", "context"):
        p = sub.add_parser(name)
        p.add_argument("--profile", default="personal")
        p.add_argument("--private", help="checkout repo riêng (có thư mục skills/); mặc định $MAH_PRIVATE_DIR")
        if name == "install":
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--keep-legacy-hooks", action="store_true", help="không gỡ hook llmwiki cũ")
            p.add_argument("--force-docs", action="store_true", help="thay CLAUDE.md/RTK.md đang khác (có sao lưu)")
            p.add_argument("--with-moli", action="store_true", help="tải và chạy script cài Moli chính thức (mạng)")
        if name == "check":
            p.add_argument("--json", action="store_true")
    args = ap.parse_args()
    return {"install": install, "check": check, "context": context}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
