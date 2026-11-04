#!/usr/bin/env python3
"""harness-replay — chạy engine + policy ỨNG VIÊN trên lịch sử tool-call thật, đo blast radius.

Câu hỏi nó trả lời (mượn "conservativity" của open-ontologies): sửa luật / regex / engine thế này thì
bao nhiêu lệnh TRƯỚC ĐÂY được qua giờ sẽ bị chặn, và bao nhiêu lệnh trước đây bị chặn giờ được qua?

Dữ liệu (ở <dự án>/.claude/audit/):
  audit.jsonl      R4 — tool-call đã CHẠY → verdict cũ = cho qua
  decisions.jsonl  #3 — tool-call bị CHẶN → verdict cũ = chặn (kèm rule)
Engine ứng viên: bin/ cạnh file này (hoặc --engine DIR) — gọi CÙNG hàm thuần mà hook dùng:
  llmwiki-validate.evaluate()       luật nội dung (R20, deny_write…)
  harness-events.REPLAYABLE[action] hook_event chặn (R22…)

Giới hạn — in ra ở mỗi lần chạy, không giấu:
  - Write/Edit đo trên nội dung HIỆN TẠI của file trên đĩa, không phải nội dung lúc ghi. File đã xoá → "không đo được".
  - Lệnh Bash là bản ĐÃ CHE secret (R4), không phải lệnh gốc.
  - Audit trước 2026-11-04 không ghi Bash → luật Bash chỉ đo được trên dữ liệu từ sau ngày đó.
  - Hook chặn không khai trong REPLAYABLE → liệt kê là "không replay được".

Usage:
  harness-replay.py [--project DIR ...] [--engine DIR] [--policy FILE] [--examples N] [--summary]
                    [--fail-on-new-blocks]
Exit: 0 · 1 khi --fail-on-new-blocks và có lệnh cũ giờ bị chặn · 2 lỗi đầu vào
"""
import argparse
import collections
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WRITE_TOOLS = ("Write", "Edit", "MultiEdit")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Engine:
    def __init__(self, engine_dir, policy_path):
        sys.path.insert(0, engine_dir)   # để engine import đúng harness_audit cùng thư mục
        self.val = load_module("oo_validate", os.path.join(engine_dir, "llmwiki-validate.py"))
        self.ev = load_module("oo_events", os.path.join(engine_dir, "harness-events.py"))
        self.policy = self.val.load_policy(policy_path)
        if self.policy is None:
            raise SystemExit(f"harness-replay: không đọc được policy {policy_path}")
        replayable = getattr(self.ev, "REPLAYABLE", {})
        self.hooks, self.unreplayable = [], []
        for r in (self.policy.get("rules") or {}).values():
            if r.get("kind") != "hook_event" or not r.get("blocking") or r.get("event") != "PreToolUse":
                continue
            if "session" not in (r.get("enforce_at") or []):
                continue
            fn = replayable.get(r.get("event_action"))
            if fn is None:
                self.unreplayable.append(r.get("id", "?"))
            else:
                self.hooks.append((r, re.compile(r.get("matcher") or ".*"), fn))

    def verdict(self, tool, ti):
        """→ (rule_id | None). Thứ tự giống wiring: cổng nội dung trước, hook_event sau."""
        for r, _ in self.val.evaluate(self.policy, tool, ti):
            return r.get("id", "?")
        if tool == "Bash":
            for r, matcher, fn in self.hooks:
                if matcher.fullmatch(tool) and fn(ti.get("command") or ""):
                    return r.get("id", "?")
        return None


def records(project):
    d = os.path.join(project, ".claude", "audit")
    sys.path.insert(0, HERE)
    import harness_audit as HA
    out = []
    for e in HA.read_jsonl(os.path.join(d, "audit.jsonl")):
        tool = e.get("tool")
        if tool in WRITE_TOOLS and e.get("path"):
            out.append((tool, e["path"], None, e.get("ts", "")))
        elif tool == "Bash" and e.get("cmd") is not None:
            out.append((tool, e["cmd"], None, e.get("ts", "")))
    for e in HA.read_jsonl(os.path.join(d, "decisions.jsonl")):
        if e.get("tool") and e.get("subject") is not None:
            out.append((e["tool"], e["subject"], e.get("rule") or "?", e.get("ts", "")))
    return out


def replay(engine, project):
    st = collections.Counter()
    new_blocks = collections.defaultdict(list)   # rule → [subject]
    new_allows = collections.defaultdict(list)   # rule cũ → [subject]
    changed_rule = []
    old_env, old_cwd = os.environ.get("CLAUDE_PROJECT_DIR"), os.getcwd()
    # Hook thật chạy với cwd = gốc dự án và CLAUDE_PROJECT_DIR = gốc dự án → dựng lại đúng môi trường đó,
    # để đường dẫn tương đối trong audit được engine đọc như lúc ghi.
    os.environ["CLAUDE_PROJECT_DIR"] = project
    try:
        os.chdir(project)
    except OSError:
        pass
    try:
        for tool, subject, old, _ts in records(project):
            st["tổng"] += 1
            if tool in WRITE_TOOLS:
                p = subject if os.path.isabs(subject) else os.path.join(project, subject)
                if not os.path.isfile(p):
                    st["không đo được (file không còn)"] += 1
                    continue
                ti = {"file_path": subject}
            else:
                ti = {"command": subject}
            try:
                new = engine.verdict(tool, ti)
            except Exception as e:   # engine ứng viên hỏng trên một input → đếm, không dừng cả lượt
                st["engine lỗi"] += 1
                new_blocks[f"LỖI {type(e).__name__}"].append(subject)
                continue
            if old is None and new is None:
                st["vẫn qua"] += 1
            elif old is not None and new is not None:
                st["vẫn chặn"] += 1
                if old != new:
                    changed_rule.append((old, new, subject))
            elif new is not None:
                st["MỚI BỊ CHẶN"] += 1
                new_blocks[new].append(subject)
            else:
                st["mới được qua"] += 1
                new_allows[old].append(subject)
    finally:
        os.chdir(old_cwd)
        if old_env is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = old_env
    return st, new_blocks, new_allows, changed_rule


def short(s, n=110):
    s = (s or "").replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", action="append", default=[])
    ap.add_argument("--engine", default=HERE, help="thư mục bin/ của engine ứng viên")
    ap.add_argument("--policy", help="policy ứng viên (mặc định <engine>/../policy.yaml)")
    ap.add_argument("--examples", type=int, default=3)
    ap.add_argument("--summary", action="store_true", help="vài dòng, cho harness-plan nhúng")
    ap.add_argument("--fail-on-new-blocks", action="store_true")
    a = ap.parse_args()
    engine_dir = os.path.abspath(a.engine)
    policy = a.policy or os.path.normpath(os.path.join(engine_dir, "..", "policy.yaml"))
    eng = Engine(engine_dir, policy)
    projects = a.project or [os.environ.get("CLAUDE_PROJECT_DIR", ".")]

    any_new = False
    for proj in projects:
        proj = os.path.abspath(os.path.expanduser(proj))
        st, nb, na, cr = replay(eng, proj)
        any_new |= bool(nb)
        if a.summary:
            if not st["tổng"]:
                print("replay: chưa có audit để đo")
                continue
            print(f"replay {st['tổng']} lệnh: {st['MỚI BỊ CHẶN']} MỚI BỊ CHẶN · {st['mới được qua']} mới được qua · "
                  f"{st['không đo được (file không còn)']} không đo được")
            for rule, subs in sorted(nb.items(), key=lambda x: -len(x[1])):
                print(f"  {rule}: {len(subs)} lệnh, vd {short(subs[0], 80)}")
            continue
        print(f"harness replay · {proj}")
        print(f"  engine: {engine_dir}")
        print(f"  policy: {policy}")
        if eng.unreplayable:
            print(f"  không replay được (hook chặn chưa khai REPLAYABLE): {', '.join(eng.unreplayable)}")
        print("  lưu ý: Write/Edit đo trên nội dung HIỆN TẠI của file; Bash là lệnh đã che secret.")
        print()
        for k in ("tổng", "vẫn qua", "vẫn chặn", "MỚI BỊ CHẶN", "mới được qua",
                  "không đo được (file không còn)", "engine lỗi"):
            if st[k] or k in ("tổng", "MỚI BỊ CHẶN", "mới được qua"):
                print(f"  {k:<32} {st[k]}")
        for title, group in (("MỚI BỊ CHẶN (trước đây qua)", nb), ("Mới được qua (trước đây bị chặn)", na)):
            if not group:
                continue
            print(f"\n{title}:")
            for rule, subs in sorted(group.items(), key=lambda x: -len(x[1])):
                uniq = list(dict.fromkeys(subs))
                print(f"  {rule}: {len(subs)} lệnh ({len(uniq)} khác nhau)")
                for s in uniq[:a.examples]:
                    print(f"    - {short(s)}")
        if cr:
            print("\nVẫn chặn nhưng bởi luật khác:")
            for o, n, s in cr[:a.examples]:
                print(f"  {o} → {n}: {short(s)}")
        print()
    return 1 if (a.fail_on_new_blocks and any_new) else 0


if __name__ == "__main__":
    sys.exit(main())
