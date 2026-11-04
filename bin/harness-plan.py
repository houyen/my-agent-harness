#!/usr/bin/env python3
"""harness-plan — xem trước hệ quả của một thay đổi luật TRƯỚC khi sinh/cài (kiểu `terraform plan`).

So bản ĐANG SỬA (working tree) với một mốc git (mặc định HEAD) trên ba mặt:
  1. Luật (policy.yaml): thêm / bỏ / đổi trường, phân loại CHẶT hơn hay LỎNG hơn, chấm rủi ro.
  2. Engine (bin/*.py): logic một số luật nằm trong code (R22 ở harness-events.py, R20 ở
     llmwiki-validate.py) → đổi code cũng là đổi luật, dù policy.yaml không đổi một dòng.
  3. Wiring sinh ra (out/): chạy gen-converters của CẢ HAI phiên bản trong thư mục tạm rồi diff.
     Không ghi gì vào out/ thật: plan không có tác dụng phụ.
Thêm --projects / --discover: với mỗi dự án đã cài, báo policy đang cài khớp mốc, khớp bản mới, hay
đã bị sửa tay (lệch cả hai), và — khi có audit — chạy harness-replay để đếm lệnh cũ giờ bị chặn.

Rủi ro: high  = có chỗ CHẶN mới / chặt hơn ở layer session (agent bị chặn ngay giữa phiên),
                hoặc đổi engine của luật đang chặn (chưa đo được bằng đọc policy).
        medium = CI/pre-commit có thể đỏ (layer repo), đổi matcher, giảm/bỏ một lớp bảo vệ.
        low    = chỉ đổi lời văn, handler, timeout, hoặc nới lỏng luật không chặn.

Usage:
  harness-plan.py [--base REF] [--projects DIR ...] [--discover DIR] [--diff] [--no-replay]
                  [--fail-on high|medium]
Exit: 0 · 1 khi rủi ro ≥ --fail-on · 2 lỗi đầu vào
"""
import argparse
import difflib
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    sys.exit("harness-plan: cần pyyaml (pip install pyyaml)")

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, ".."))
INSTALLED_REL = "harness/poc-vendor-neutral"
RANK = {"low": 0, "medium": 1, "high": 2}

# trường danh sách: thêm phần tử thì luật CHẶT hơn (strict) hay LỎNG hơn (loose)
STRICT_ON_ADD = {"target_globs", "deny_write_globs", "require_keys", "need_contains",
                 "forbid_contains", "root_globs"}
LOOSE_ON_ADD = {"exclude_basenames", "valid_entity_types", "allow_basenames", "allow_subdirs",
                "when_contains"}
TEXT_ONLY = {"statement", "statement_en", "handler", "timeout", "name"}
CONTENT_KINDS = {"deny_write", "require_section", "forbid_root", "require_frontmatter",
                 "conditional_require"}


def sha(data):
    return hashlib.sha256(data).hexdigest()[:16]


def git(*args):
    r = subprocess.run(["git", "-C", HARNESS, *args], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def base_file(ref, rel):
    """Nội dung file ở mốc git (đường dẫn tương đối so với thư mục harness), None nếu không có."""
    prefix = (git("rev-parse", "--show-prefix") or b"").decode().strip()
    return git("show", f"{ref}:{prefix}{rel}")


def blocks_at_session(r):
    if "session" not in (r.get("enforce_at") or []):
        return False
    if r.get("kind") == "hook_event":
        return bool(r.get("blocking"))
    return r.get("kind") in CONTENT_KINDS


def blocks_at_repo(r):
    return "repo" in (r.get("enforce_at") or []) and r.get("kind") in CONTENT_KINDS


def tighten_risk(r):
    return "high" if blocks_at_session(r) else ("medium" if blocks_at_repo(r) else "low")


def diff_rule(name, old, new):
    """→ list (risk, mô tả) cho một luật có ở cả hai bản."""
    out = []
    rid = new.get("id", name)
    for k in sorted(set(old) | set(new)):
        a, b = old.get(k), new.get(k)
        if a == b:
            continue
        if k in TEXT_ONLY:
            out.append(("low", f"{rid}: đổi {k}"))
        elif k == "kind":
            out.append(("high", f"{rid}: đổi kind {a} → {b}"))
        elif k == "blocking":
            if b and not a:
                out.append(("high" if "session" in (new.get("enforce_at") or []) else "medium",
                            f"{rid}: blocking false → true (từ giờ CHẶN)"))
            else:
                out.append(("medium", f"{rid}: blocking true → false (bỏ một lớp chặn)"))
        elif k == "enforce_at":
            add, rem = set(b or []) - set(a or []), set(a or []) - set(b or [])
            if "session" in add and new.get("kind") in CONTENT_KINDS | {"hook_event"}:
                out.append(("high" if blocks_at_session(new) else "low", f"{rid}: thêm layer session"))
            if "repo" in add and new.get("kind") in CONTENT_KINDS:
                out.append(("medium", f"{rid}: thêm layer repo (CI/pre-commit có thể đỏ)"))
            if rem:
                out.append(("medium", f"{rid}: bỏ layer {', '.join(sorted(rem))} (giảm bảo vệ)"))
        elif k == "matcher" or k == "event":
            out.append(("medium", f"{rid}: đổi {k} {a!r} → {b!r} (hook bắt tập tool khác)"))
        elif isinstance(a, list) or isinstance(b, list):
            add = [x for x in (b or []) if x not in (a or [])]
            rem = [x for x in (a or []) if x not in (b or [])]
            stricter = (k in STRICT_ON_ADD and add) or (k in LOOSE_ON_ADD and rem)
            looser = (k in STRICT_ON_ADD and rem) or (k in LOOSE_ON_ADD and add)
            detail = " ".join([f"+{x}" for x in add] + [f"-{x}" for x in rem])
            if stricter:
                out.append((tighten_risk(new), f"{rid}: {k} CHẶT hơn ({detail})"))
            if looser:
                out.append(("low", f"{rid}: {k} lỏng hơn ({detail})"))
            if not stricter and not looser:
                out.append(("medium", f"{rid}: đổi {k} ({detail})"))
        elif k == "require_body" and b and not a:
            out.append((tighten_risk(new), f"{rid}: require_body false → true (CHẶT hơn)"))
        else:
            out.append(("medium", f"{rid}: đổi {k} {a!r} → {b!r}"))
    return out


def diff_policy(old, new):
    o, n = (old or {}).get("rules") or {}, (new or {}).get("rules") or {}
    out = []
    for name in sorted(set(n) - set(o)):
        r = n[name]
        risk = "high" if blocks_at_session(r) else ("medium" if blocks_at_repo(r) else "low")
        out.append((risk, f"+ {r.get('id', name)} {r.get('name', name)} (luật mới"
                          f"{', CHẶN ở session' if risk == 'high' else ''})"))
    for name in sorted(set(o) - set(n)):
        r = o[name]
        blocking = blocks_at_session(r) or blocks_at_repo(r)
        out.append(("medium" if blocking else "low",
                    f"- {r.get('id', name)} {r.get('name', name)} (bỏ luật{' đang chặn' if blocking else ''})"))
    for name in sorted(set(o) & set(n)):
        out += diff_rule(name, o[name], n[name])
    return out


def engine_rules(policy):
    """Engine file → luật đang chặn mà logic nằm trong file đó."""
    m = {}
    for r in ((policy or {}).get("rules") or {}).values():
        if r.get("kind") == "hook_event" and r.get("blocking"):
            m.setdefault("harness-events.py", []).append(r.get("id"))
        elif r.get("kind") in CONTENT_KINDS:
            m.setdefault("llmwiki-validate.py", []).append(r.get("id"))
    return m


def diff_engines(ref, policy):
    out = []
    owners = engine_rules(policy)
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".py"):
            continue
        cur = open(os.path.join(HERE, f), "rb").read()
        old = base_file(ref, f"bin/{f}")
        if old == cur:
            continue
        rules = owners.get(f)
        if old is None:
            out.append(("low", f"engine mới: bin/{f}"))
        elif rules:
            out.append(("high", f"engine bin/{f} đổi → logic của {', '.join(rules)} có thể đổi "
                                f"(policy không thấy được; xem replay bên dưới)"))
        else:
            out.append(("low", f"engine bin/{f} đổi (không chứa luật chặn)"))
    return out


def generate(work, policy_bytes, gen_bytes):
    """Chạy gen-converters trong thư mục tạm → trả về {đường_dẫn_tương_đối: bytes}."""
    os.makedirs(work, exist_ok=True)
    open(os.path.join(work, "policy.yaml"), "wb").write(policy_bytes)
    open(os.path.join(work, "gen-converters.py"), "wb").write(gen_bytes)
    r = subprocess.run([sys.executable, "gen-converters.py"], cwd=work, capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr.strip() or r.stdout.strip()
    files = {}
    out = os.path.join(work, "out")
    for dp, _, fs in os.walk(out):
        for f in fs:
            p = os.path.join(dp, f)
            files[os.path.relpath(p, out)] = open(p, "rb").read()
    return files, None


def diff_outputs(base, cand, show):
    out, lines = [], []
    for f in sorted(set(base) | set(cand)):
        a, b = base.get(f), cand.get(f)
        if a == b:
            continue
        tag = "+" if a is None else ("-" if b is None else "~")
        out.append(f"{tag} out/{f}")
        if show and a is not None and b is not None:
            lines += difflib.unified_diff(a.decode(errors="replace").splitlines(),
                                          b.decode(errors="replace").splitlines(),
                                          f"base/out/{f}", f"plan/out/{f}", lineterm="", n=1)
    return out, lines


def discover(top, depth=4):
    found = []
    top = os.path.abspath(os.path.expanduser(top))
    base_depth = top.rstrip(os.sep).count(os.sep)
    for dp, dns, _ in os.walk(top):
        if dp.count(os.sep) - base_depth >= depth:
            dns[:] = []
        dns[:] = [d for d in dns if not d.startswith(".") and d not in ("node_modules", "vendor")]
        if os.path.isfile(os.path.join(dp, INSTALLED_REL, "policy.yaml")):
            found.append(dp)
    return found


_HISTORY = None


def policy_history():
    """{sha16 policy.yaml: 'commit ngày'} cho mọi phiên bản policy.yaml trong lịch sử git harness."""
    global _HISTORY
    if _HISTORY is None:
        _HISTORY = {}
        prefix = (git("rev-parse", "--show-prefix") or b"").decode().strip()
        log = (git("log", "--format=%h %ad", "--date=short", "--", "policy.yaml") or b"").decode()
        for line in log.splitlines():
            h = line.split()[0]
            data = git("show", f"{h}:{prefix}policy.yaml")
            if data is not None:
                _HISTORY.setdefault(sha(data), line)
    return _HISTORY


def project_report(p, base_sha, cand_sha, cand_policy, replay):
    pol = os.path.join(p, INSTALLED_REL, "policy.yaml")
    if not os.path.isfile(pol):
        return [f"  {p}: chưa cài harness (không có {INSTALLED_REL}/policy.yaml)"]
    raw = open(pol, "rb").read()
    s = sha(raw)
    try:
        inst = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        inst = {}
    n = len(inst.get("rules") or {})
    if s == cand_sha:
        state = f"{n} luật · đã khớp bản mới (cài lại không đổi policy)"
    elif s == base_sha:
        state = f"{n} luật · đang ở mốc → SẼ ĐỔI khi cài lại"
    elif s in policy_history():
        state = f"{n} luật · bản cũ (commit {policy_history()[s]}) → SẼ ĐỔI khi cài lại"
    else:
        state = f"{n} luật · không khớp phiên bản nào trong lịch sử (sửa tay?) → cài lại sẽ GHI ĐÈ"
    lines = [f"  {p}: {state}"]
    if s != cand_sha:
        ch = diff_policy(inst, cand_policy)
        added = [m for _, m in ch if m.startswith("+ ")]
        removed = [m for _, m in ch if m.startswith("- ")]
        high = [m for r, m in ch if r == "high"]
        lines.append(f"      cài lại: +{len(added)} luật · -{len(removed)} luật · "
                     f"{len(ch) - len(added) - len(removed)} thay đổi khác · {len(high)} high")
        lines += [f"      [high] {m}" for m in high[:5]]
    if replay:
        r = subprocess.run([sys.executable, os.path.join(HERE, "harness-replay.py"), "--project", p,
                            "--summary"], capture_output=True, text=True)
        txt = (r.stdout or r.stderr).strip()
        lines += [f"      {x}" for x in txt.splitlines()] if txt else []
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="HEAD", help="mốc git để so (mặc định HEAD)")
    ap.add_argument("--projects", nargs="*", default=[])
    ap.add_argument("--discover", help="tìm dự án đã cài harness dưới thư mục này (sâu ≤4)")
    ap.add_argument("--diff", action="store_true", help="in unified diff của out/")
    ap.add_argument("--no-replay", action="store_true", help="không chạy harness-replay cho dự án")
    ap.add_argument("--fail-on", choices=["high", "medium"])
    a = ap.parse_args()

    cand_pol = open(os.path.join(HARNESS, "policy.yaml"), "rb").read()
    cand_gen = open(os.path.join(HARNESS, "gen-converters.py"), "rb").read()
    base_pol = base_file(a.base, "policy.yaml")
    base_gen = base_file(a.base, "gen-converters.py")
    if base_pol is None:
        print(f"(không đọc được policy.yaml ở mốc {a.base} — coi mốc là rỗng)")
        base_pol = b"rules: {}\n"
    if base_gen is None:
        base_gen = cand_gen
    try:
        cand_policy = yaml.safe_load(cand_pol) or {}
        base_policy = yaml.safe_load(base_pol) or {}
    except yaml.YAMLError as e:
        print(f"harness-plan: policy.yaml lỗi YAML: {e}", file=sys.stderr)
        return 2

    changes = diff_policy(base_policy, cand_policy) + diff_engines(a.base, cand_policy)
    tmp = tempfile.mkdtemp(prefix="harness-plan-")
    bo, err1 = generate(os.path.join(tmp, "base"), base_pol, base_gen)
    co, err2 = generate(os.path.join(tmp, "plan"), cand_pol, cand_gen)
    if err2:
        print(f"harness-plan: gen-converters bản mới lỗi: {err2}", file=sys.stderr)
        shutil.rmtree(tmp, ignore_errors=True)
        return 2
    outs, udiff = diff_outputs(bo or {}, co, a.diff)
    if err1:
        outs.insert(0, f"(gen-converters ở mốc lỗi, so với rỗng: {err1.splitlines()[-1]})")
    shutil.rmtree(tmp, ignore_errors=True)

    risk = max([RANK[r] for r, _ in changes], default=0)
    level = {v: k for k, v in RANK.items()}[risk]
    print(f"harness plan · mốc {a.base} → working tree")
    print(f"  luật: {len(base_policy.get('rules') or {})} → {len(cand_policy.get('rules') or {})}")
    print()
    print("Thay đổi luật / engine:")
    if not changes:
        print("  (không có)")
    for r, msg in sorted(changes, key=lambda x: -RANK[x[0]]):
        print(f"  [{r:<6}] {msg}")
    print()
    print("Wiring sinh ra (out/):")
    print("\n".join(f"  {x}" for x in outs) if outs else "  (không đổi)")
    for line in udiff:
        print("    " + line)

    projects = list(a.projects)
    if a.discover:
        projects += discover(a.discover)
    if projects:
        print()
        print("Dự án đã cài (blast radius):")
        for p in dict.fromkeys(os.path.abspath(os.path.expanduser(x)) for x in projects):
            for line in project_report(p, sha(base_pol), sha(cand_pol), cand_policy, not a.no_replay):
                print(line)
    print()
    print(f"risk_score: {level}")
    if a.fail_on and risk >= RANK[a.fail_on]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
