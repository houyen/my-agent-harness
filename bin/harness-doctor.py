#!/usr/bin/env python3
"""Read-only diagnostics for a harness checkout and local installations."""

import argparse
from collections import defaultdict
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tomllib


CHECKSUM = re.compile(r"([0-9a-fA-F]{64}) [ *](.+)")
VISIBILITY = ("on", "name-only", "user-invocable-only", "off")
USAGE_FILES = ("claude.py", "codex_mcp.py", "core.py", "rates.json")
BINARIES = ("moli", "orca", "browser-use", "trivy", "gh", "rtk", "codex", "claude", "opencode")
HOOK_PATH = "harness/poc-vendor-neutral/bin/codex-hook.py"
HOOK_STATUS = "my-agent-harness PreToolUse"


def children(directory):
    try:
        return sorted(directory.iterdir())
    except FileNotFoundError:
        return []


def digest(path):
    if not path.is_file():
        raise ValueError(f"{path}: cần file thường")
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def tree(directory, ancestors=frozenset()):
    """Hash files by relative path, including files reached through symlinks."""
    info = directory.stat()
    identity = (info.st_dev, info.st_ino)
    if identity in ancestors:
        raise ValueError(f"vòng lặp symlink: {directory}")
    ancestors = ancestors | {identity}
    entries = {}
    for path in sorted(directory.iterdir()):
        if stat.S_ISDIR(path.stat().st_mode):
            for name, value in tree(path, ancestors).items():
                entries[f"{path.name}/{name}"] = value
        else:
            entries[path.name] = digest(path)
    return entries


def git(directory, *args):
    return subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-c",
         "core.untrackedCache=false", "-C", str(directory), *args],
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
        check=True, capture_output=True, text=True, errors="replace",
    ).stdout.strip()


def repository(report, source):
    root = Path(git(source, "rev-parse", "--show-toplevel"))
    report("OK", f"root: {root}")
    report("OK", f"HEAD: {git(root, 'rev-parse', 'HEAD')}")
    dirty = git(root, "status", "--porcelain=v1", "--untracked-files=normal")
    report("WARN" if dirty else "OK", f"thay đổi chưa commit: {'có' if dirty else 'không'}")


def vendored(report, directory, skills):
    expected = {}
    for number, line in enumerate((directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines(), 1):
        match = CHECKSUM.fullmatch(line)
        if not match:
            report("FAIL", f"SHA256SUMS dòng {number}: sai định dạng")
            continue
        checksum, name = match.groups()
        parts = name.split("/")
        if name in expected or any(part in ("", ".", "..") for part in parts) or name == "SHA256SUMS":
            report("FAIL", f"SHA256SUMS dòng {number}: đường dẫn không hợp lệ hoặc trùng")
            continue
        expected[name] = checksum.lower()

    actual = {}
    notice = directory / "NOTICE.md"
    if notice.is_file():
        actual[notice.name] = digest(notice)
    for skill, files in skills.items():
        actual.update({f"{skill}/{name}": value for name, value in files.items()})
    for name in sorted(expected.keys() - actual.keys()):
        report("FAIL", f"thiếu file: {name}")
    for name in sorted(actual.keys() - expected.keys()):
        report("FAIL", f"thừa file: {name}")
    for name in sorted(actual.keys() & expected.keys()):
        if actual[name] != expected[name]:
            report("FAIL", f"sai checksum: {name}")
    if actual == expected and actual:
        report("OK", f"SHA256SUMS khớp ({len(actual)} file)")
    elif not expected:
        report("FAIL", "SHA256SUMS không có mục hợp lệ")


def installed(report, home):
    locations = {}
    targets = defaultdict(dict)
    for label in (".agents", ".claude"):
        skills = locations[label] = {}
        for path in children(home / label / "skills"):
            if path.name in {"synced", ".trash"}:
                continue
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                destination = os.readlink(path)
                try:
                    target = path.resolve(strict=True)
                except (FileNotFoundError, NotADirectoryError, RuntimeError):
                    report("WARN", f"symlink hỏng: {label}/skills/{path.name} → {destination}")
                    continue
                except OSError as error:
                    # Python 3.13+ reports a symlink loop as ELOOP.
                    if error.errno != errno.ELOOP:
                        raise
                    report("WARN", f"symlink hỏng: {label}/skills/{path.name} → {destination}")
                    continue
            elif stat.S_ISDIR(mode):
                target = path.resolve()
            else:
                continue
            target_stat = target.stat()
            if not stat.S_ISDIR(target_stat.st_mode):
                continue
            skills[path.name] = target
            targets[(target_stat.st_dev, target_stat.st_ino)][path.name] = target
    for names in targets.values():
        if len(names) > 1:
            report("OK", f"alias: {', '.join(sorted(names))} → {min(names.values())}")
    return locations


def installed_contents(report, sources, locations, alias_report):
    cache = {}

    def files(path):
        if path not in cache:
            cache[path] = tree(path)
        return cache[path]

    for name, source in sources.items():
        for label, skills in locations.items():
            path = skills.get(name)
            if path is None:
                result = "chưa cài"
            else:
                result = "khớp" if files(path) == source else "lệch"
            report("OK" if result == "khớp" else "WARN", f"{label}/skills/{name}: {result}")

    agents, claude = locations[".agents"], locations[".claude"]
    for name in sorted(agents.keys() & claude.keys()):
        if agents[name] != claude[name] and files(agents[name]) != files(claude[name]):
            alias_report("WARN", f"cùng tên, khác nội dung ở .agents và .claude: {name}")


def mapping(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label}: cần một bảng")
    return value


def read_config(report, path, parse):
    try:
        return mapping(parse(path.read_text(encoding="utf-8")), path)
    except FileNotFoundError:
        report("WARN", f"thiếu {path}")
        return {}


def show_names(report, severity, label, names):
    if names:
        report(severity, f"{label}: {', '.join(sorted(names))}")


def skill_lock(report, home, names, sources):
    data = read_config(report, home / ".agents" / ".skill-lock.json", json.loads)
    locked = mapping(data.get("skills", {}), "skills trong lock").keys()
    show_names(report, "WARN", "có trong lock, thiếu trên đĩa", locked - names)
    show_names(report, "OK", "có trên đĩa, ngoài lock (bình thường với skill do harness quản)", names - locked)
    show_names(report, "WARN", "vendored có trong lock; npx skills update sẽ đè lên", locked & sources.keys())


def claude_settings(report, home, names):
    data = read_config(report, home / ".claude" / "settings.json", json.loads)
    overrides = mapping(data.get("skillOverrides", {}), "skillOverrides")
    grouped = defaultdict(list)
    for name in sorted(names | overrides.keys()):
        value = overrides.get(name, "on")
        if value not in VISIBILITY:
            report("FAIL", f"skillOverrides.{name}: giá trị không hợp lệ ({value!r})")
        else:
            grouped[value].append(name)
    for value in VISIBILITY:
        show_names(report, "OK", value, grouped[value])
    show_names(report, "WARN", "override không khớp skill nào", overrides.keys() - names)


def codex_config(report, codex_home):
    data = read_config(report, codex_home / "config.toml", tomllib.loads)
    servers = mapping(data.get("mcp_servers", {}), "mcp_servers")
    tui = mapping(data.get("tui", {}), "tui")
    for label, present in (
        ("[mcp_servers.agent-usage]", isinstance(servers.get("agent-usage"), dict)),
        ("tui.status_line_provider", "status_line_provider" in tui),
    ):
        report("OK" if present else "WARN", f"{label}: {'có' if present else 'thiếu'}")


def project_hook(report, project):
    path = project / ".codex" / "hooks.json"
    data = read_config(report, path, json.loads)
    events = mapping(data.get("hooks", {}), "hooks")
    groups = events.get("PreToolUse", [])
    if not isinstance(groups, list):
        raise ValueError(f"{path}: PreToolUse cần một danh sách")
    found = False
    for group in groups:
        hooks = mapping(group, "PreToolUse group").get("hooks", [])
        if not isinstance(hooks, list):
            raise ValueError(f"{path}: hooks trong PreToolUse cần một danh sách")
        for hook in hooks:
            entry = mapping(hook, "PreToolUse hook")
            command = entry.get("command")
            if (entry.get("type") == "command" and entry.get("statusMessage") == HOOK_STATUS
                    and isinstance(command, str) and HOOK_PATH in command):
                found = True
    if found:
        report("OK", f"{path}: cấu hình có mặt; trust: chưa xác minh (xem /hooks trong Codex)")
    else:
        report("WARN", f"{path}: thiếu entry của harness")


def usage(report, source, destination):
    for name in USAGE_FILES:
        path = destination / name
        if not path.exists():
            report("WARN", f"{path}: thiếu")
        else:
            matches = digest(path) == digest(source / name)
            report("OK" if matches else "WARN", f"{path}: {'khớp' if matches else 'lệch'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", help="In báo cáo JSON")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME") or home / ".codex")
    usage_home = Path(os.environ.get("AGENT_USAGE_HOME") or home / ".agent-usage")
    sections = {name: [] for name in (
        "Repo harness", "Skill vendored", "Skill đã cài", "Lock", "Hiển thị ở Claude",
        "Alias và symlink", "Dependency", "Codex", "Thanh usage",
    )}

    def reporter(section):
        def report(status, message):
            sections[section].append({"status": status, "message": message})
        return report

    def check(section, inspect, *params):
        report = reporter(section)
        try:
            return inspect(report, *params)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            report("FAIL", str(error))

    check("Repo harness", repository, source)
    directory = source / "skills"

    def scan_vendored(_report):
        return {path.name: tree(path) for path in children(directory) if path.is_dir()}

    sources = check("Skill vendored", scan_vendored)
    if sources is not None:
        check("Skill vendored", vendored, directory, sources)
    locations = check("Alias và symlink", installed, home)
    if locations is not None:
        names = set().union(*(skills.keys() for skills in locations.values()))
        check("Skill đã cài", installed_contents, sources or {}, locations, reporter("Alias và symlink"))
        check("Lock", skill_lock, home, names, sources or {})
        check("Hiển thị ở Claude", claude_settings, home, names)
    dependency = reporter("Dependency")
    for binary in BINARIES:
        dependency("OK", f"{binary}: {shutil.which(binary) or 'không có'}")
    check("Codex", codex_config, codex_home)
    check("Codex", project_hook, args.project.absolute())
    check("Thanh usage", usage, source / "bin" / "usage", usage_home)

    for section, rows in sections.items():
        if rows:
            continue
        if locations is None or (section == "Skill đã cài" and sources is None):
            reporter(section)("WARN", "không có kết quả vì không đọc được danh sách skill")
        else:
            reporter(section)("OK", "không có mục để báo")
    if args.json:
        print(json.dumps(sections, ensure_ascii=False, indent=2))
    else:
        for section, rows in sections.items():
            print(f"── {section} ──")
            for row in rows:
                print(f"{row['status']} {' | '.join(row['message'].splitlines())}")
    return int(any(row["status"] == "FAIL" for rows in sections.values() for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
