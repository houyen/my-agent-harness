#!/usr/bin/env python3
"""Adapt Codex PreToolUse to the shared R22 and R20 rules."""
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


FILE_HEADER = re.compile(r"\*\*\* (Add|Update|Delete) File: (.+)")
MOVE_HEADER = "*** Move to: "
EOF_HEADER = "*** End of File"


def patch_files(patch):
    """Yield file sections in the order used by apply_patch."""
    lines = patch.strip("\r\n").replace("\r\n", "\n").split("\n")
    if lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("patch thiếu Begin Patch hoặc End Patch")
    lines = lines[1:-1]
    start = 0
    while start < len(lines):
        match = FILE_HEADER.fullmatch(lines[start])
        if not match:
            raise ValueError(f"header patch không hợp lệ: {lines[start]}")
        end = start + 1
        while end < len(lines) and not FILE_HEADER.fullmatch(lines[end]):
            end += 1
        action, path = match.groups()
        yield action, path, lines[start + 1:end]
        start = end


def find_context(lines, context, start, at_end=False):
    if not context:
        return len(lines)
    last = len(lines) - len(context)
    offsets = (last,) if at_end and last >= start else range(start, last + 1)
    # Codex tries exact matches before falling back to whitespace-insensitive matches.
    for normalize in (lambda line: line, str.rstrip, str.strip):
        expected = [normalize(line) for line in context]
        for offset in offsets:
            actual = lines[offset:offset + len(context)]
            if [normalize(line) for line in actual] == expected:
                return offset
    raise ValueError("không tìm thấy context của hunk")


def update_content(content, patch_lines):
    original = content.split("\n")
    if original[-1] == "":
        original.pop()
    result = []
    cursor = 0
    index = 0
    while index < len(patch_lines):
        line = patch_lines[index]
        cursor_after_anchor = cursor
        if line == "@@" or line.startswith("@@ "):
            if line.startswith("@@ "):
                cursor_after_anchor = find_context(original, [line[3:]], cursor) + 1
            index += 1
        elif index != 0:
            raise ValueError(f"header hunk không hợp lệ: {line}")
        before, after = [], []
        while index < len(patch_lines):
            line = patch_lines[index]
            if not line.startswith((" ", "+", "-")) and line != "":
                break
            if not line.startswith("+"):
                before.append(line[1:])
            if not line.startswith("-"):
                after.append(line[1:])
            index += 1
        if not before and not after:
            raise ValueError("hunk rỗng")
        at_end = index < len(patch_lines) and patch_lines[index] == EOF_HEADER
        if at_end:
            index += 1
        offset = find_context(original, before, cursor_after_anchor, at_end)
        result.extend(original[cursor:offset])
        result.extend(after)
        cursor = offset + len(before)
    result.extend(original[cursor:])
    if not result or result[-1] != "":
        result.append("")
    return "\n".join(result)


def patched_contents(patch, cwd):
    """Track final contents, including paths changed by more than one section."""
    changes = {}
    for action, name, lines in patch_files(patch):
        source = Path(os.path.abspath(cwd / name))
        if action == "Delete":
            if lines:
                raise ValueError("Delete File có nội dung")
            changes[source] = None
        elif action == "Add":
            if any(not line.startswith("+") for line in lines):
                raise ValueError("Add File chứa dòng không bắt đầu bằng +")
            changes[source] = "".join(line[1:] + "\n" for line in lines)
        else:
            target = source
            if lines and lines[0].startswith(MOVE_HEADER):
                target = Path(os.path.abspath(cwd / lines[0][len(MOVE_HEADER):]))
                lines = lines[1:]
            content = changes[source] if source in changes else source.read_text(encoding="utf-8")
            if content is None:
                raise ValueError(f"file đã bị xoá trong patch: {source}")
            if target != source:
                changes[source] = None
            changes[target] = update_content(content, lines) if lines else content
    return changes


def project_root(cwd):
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True, capture_output=True
    )
    return Path(result.stdout.rstrip("\n")) if result.returncode == 0 else cwd


def decide(event, validator, policy):
    tool = event["tool_name"]
    tool_input = event["tool_input"]
    cwd = Path(event["cwd"])
    if not isinstance(tool, str) or not isinstance(tool_input, dict) or not cwd.is_absolute():
        raise ValueError("payload PreToolUse không hợp lệ")
    rules = {rule["id"]: rule for _, rule in validator.rules_for_layer(policy, "session")}
    if tool == "Bash":
        command = tool_input["command"]
        if not isinstance(command, str) and not (
            isinstance(command, list) and all(isinstance(arg, str) for arg in command)
        ):
            raise ValueError("Bash command phải là chuỗi hoặc mảng argv")
        rule = rules.get("R22", {})
        if rule.get("blocking") and os.environ.get("HARNESS_ALLOW_SYSTEM_BROWSER") != "1":
            if importlib.import_module("harness-events")._is_system_browser_cmd(command):
                return "[R22] Không mở trình duyệt hệ thống. Dùng orca tab create --url <url>."
    if tool == "apply_patch" and "R20" in rules:
        patch = tool_input.get("patch", tool_input.get("command"))
        if not isinstance(patch, str):
            raise ValueError("apply_patch thiếu nội dung patch")
        root = project_root(cwd)
        for path, content in patched_contents(patch, cwd).items():
            if content is None:
                continue
            try:
                relative = path.relative_to(root).as_posix()
            except ValueError:
                continue
            message = validator.apply_rule(rules["R20"], relative, content, None)
            if message:
                return "[R20] " + message.partition("] ")[2]
    return None


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError("payload PreToolUse phải là object")
        validator = importlib.import_module("llmwiki-validate")
        policy = validator.load_policy(validator.DEFAULT_POLICY)
        if not policy or not isinstance(policy.get("rules"), dict):
            raise ValueError(f"không đọc được policy {validator.DEFAULT_POLICY}")
        reason = decide(event, validator, policy)
        if reason:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}, ensure_ascii=False))
    except Exception as exc:
        print(f"codex-hook: fail-open: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
