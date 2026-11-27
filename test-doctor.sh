#!/usr/bin/env bash
# Test doctor against a disposable checkout, project and HOME.
set -euo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d "$PWD/out-doctor-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
python3 - "$TMP" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

root = Path(sys.argv[1])
source = Path.cwd()
repo = root / "repo"
home = root / "home"
agents = home / ".agents/skills"
claude = home / ".claude/skills"
codex = home / "custom-codex"
usage = home / "custom-usage"
project = root / "project"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def link(path, target):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(target)


shutil.copytree(source / "bin/usage", repo / "bin/usage", ignore=shutil.ignore_patterns("__pycache__"))
doctor = repo / "bin/harness-doctor.py"
shutil.copyfile(source / "bin/harness-doctor.py", doctor)
skills = repo / "skills"
for name in ("matching", "drifting", "absent"):
    write(skills / name / "SKILL.md", f"# {name}\n")
write(skills / "NOTICE.md", "Licenses\n")
manifest = skills / "SHA256SUMS"
write(manifest, "".join(
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(skills)}\n"
    for path in sorted(skills.rglob("*.md"))
))

for args in (("init", "-q"), ("add", "--", "bin", "skills"),
             ("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
              "commit", "-qm", "fixture")):
    subprocess.run(["git", "-C", str(repo), *args], check=True)

shutil.copytree(skills / "matching", agents / "matching")
shutil.copytree(skills / "drifting", agents / "drifting")
link(claude / "matching", "../../.agents/skills/matching")
link(claude / "alias", "matching")
link(claude / "broken", "nowhere")
link(claude / ".trash", "ignore-this")
write(claude / "synced/SKILL.md", "ignore this")
write(claude / "drifting/SKILL.md", "# changed\n")
write(agents / "local/SKILL.md", "# local\n")
write(home / ".agents/.skill-lock.json", '{"skills":{"matching":{},"missing":{}}}')
write(home / ".claude/settings.json", json.dumps({"skillOverrides": {
    "matching": "on", "drifting": "name-only", "alias": "user-invocable-only", "orphan": "off",
}}))
write(codex / "config.toml", '[mcp_servers.agent-usage]\ncommand = "python3"\n'
      '[tui]\nstatus_line_provider = { server = "agent-usage", tool = "statusline" }\n')
write(project / ".codex/hooks.json", json.dumps({"hooks": {"PreToolUse": [{"hooks": [{
    "type": "command", "statusMessage": "my-agent-harness PreToolUse",
    "command": 'exec python3 "$R/harness/poc-vendor-neutral/bin/codex-hook.py"',
}]}]}}))
for name in ("claude.py", "codex_mcp.py", "core.py"):
    usage.mkdir(exist_ok=True)
    shutil.copyfile(repo / "bin/usage" / name, usage / name)
write(usage / "core.py", "# changed\n")

env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(codex), "AGENT_USAGE_HOME": str(usage)}
total = passed = 0


def check(condition, description):
    global total, passed
    total += 1
    passed += bool(condition)
    print(f"  {'ok' if condition else 'NO'}  {description}")


def snapshot():
    result = {}
    for path in root.rglob("*"):
        info = path.lstat()
        content = None
        if stat.S_ISLNK(info.st_mode):
            content = os.readlink(path)
        elif stat.S_ISREG(info.st_mode):
            content = path.read_bytes()
        result[path.relative_to(root)] = (info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns, content)
    return result


def run(expected, *args, cwd=repo, json_output=False):
    before = snapshot()
    result = subprocess.run([sys.executable, str(doctor), *args], cwd=cwd, env=env,
                            text=True, capture_output=True)
    check(before == snapshot(), "doctor giữ nguyên cây HOME, project và checkout (kể cả Git index)")
    check(result.returncode == expected, f"exit {expected} (thực tế {result.returncode})")
    check(not result.stderr, "stderr trống")
    if not json_output:
        return result.stdout
    try:
        data = json.loads(result.stdout)
        check(len(data) == 9 and all(rows for rows in data.values()) and all(
            row["status"] in {"OK", "WARN", "FAIL"} and isinstance(row["message"], str)
            for rows in data.values() for row in rows
        ), "--json: 9 khối và nhãn hợp lệ")
        return "\n".join(f'{r["status"]} {r["message"]}' for rows in data.values() for r in rows)
    except (ValueError, TypeError, KeyError, AttributeError):
        check(False, "--json: cấu trúc báo cáo không hợp lệ")
        return ""


def contains(output, *lines):
    for line in lines:
        check(line in output, line)


out = run(0, "--project", str(project))
contains(out, "OK root:", "OK HEAD:", "OK thay đổi chưa commit: không",
         "OK SHA256SUMS khớp", "OK .agents/skills/matching: khớp",
         "OK .claude/skills/matching: khớp", "WARN .claude/skills/drifting: lệch",
         "WARN .agents/skills/absent: chưa cài",
         "WARN có trong lock, thiếu trên đĩa: missing",
         "OK có trên đĩa, ngoài lock (bình thường với skill do harness quản):",
         "WARN vendored có trong lock; npx skills update sẽ đè lên: matching",
         "OK on: local, matching", "OK name-only: drifting", "OK user-invocable-only: alias",
         "OK off: orphan", "WARN override không khớp skill nào: orphan",
         "OK alias: alias, matching", "WARN symlink hỏng: .claude/skills/broken",
         "WARN cùng tên, khác nội dung ở .agents và .claude: drifting",
         "OK [mcp_servers.agent-usage]: có", "OK tui.status_line_provider: có",
         "cấu hình có mặt; trust: chưa xác minh (xem /hooks trong Codex)",
         f"OK {usage}/claude.py: khớp", f"WARN {usage}/core.py: lệch",
         f"WARN {usage}/rates.json: thiếu")
check(".trash" not in out and "synced" not in out, "bỏ qua .trash và synced")
check(all(not line or line.startswith(("── ", "OK ", "WARN ", "FAIL ")) for line in out.splitlines()),
      "mỗi dòng dữ liệu có nhãn")
for binary in ("moli", "orca", "browser-use", "trivy", "gh", "rtk", "codex", "claude", "opencode"):
    contains(out, f"OK {binary}: {shutil.which(binary) or 'không có'}")

write(codex / "config.toml", 'model = "test"\n')
out = run(0, "--json", cwd=project, json_output=True)
contains(out, "WARN [mcp_servers.agent-usage]: thiếu", "WARN tui.status_line_provider: thiếu",
         "cấu hình có mặt; trust: chưa xác minh (xem /hooks trong Codex)")
check("FAIL " not in out, "WARN không làm hỏng mã thoát")

(skills / "absent/SKILL.md").unlink()
write(skills / "drifting/SKILL.md", "# changed\n")
write(skills / "matching/extra.txt", "unexpected\n")
write(codex / "config.toml", "[invalid\n")
out = run(1, "--json", json_output=True)
contains(out, "WARN thay đổi chưa commit: có", "FAIL thiếu file: absent/SKILL.md",
         "FAIL sai checksum: drifting/SKILL.md", "FAIL thừa file: matching/extra.txt",
         "FAIL Expected", "thiếu entry của harness")

print(f"\nTỔNG: {total} test · {passed} PASS · {total - passed} FAIL")
raise SystemExit(total != passed)
PY
