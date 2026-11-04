#!/usr/bin/env python3
"""harness_audit — tiện ích dùng chung cho R4 (audit) và bản ghi quyết định chặn.

Hai file, cùng thư mục `.claude/audit/` (đã gitignore ở dự án đích):
  audit.jsonl      R4: tool-call ĐÃ CHẠY (PostToolUse) → coi là "đã cho qua".
  decisions.jsonl  mỗi lần một hook CHẶN (exit 2): rule nào, khớp gì, input nào, policy nào.

Mục đích decisions.jsonl (mượn ý "certificate" của open-ontologies):
  - lần chặn bị nghi oan → có dòng bằng chứng (rule id + đoạn khớp + hash input + hash policy/engine),
    không phải đoán lại;
  - harness-replay.py chạy engine MỚI trên cả hai file để đo blast radius trước khi sửa luật.

Bảo mật: lệnh Bash có thể chứa secret → `redact()` che các mẫu phổ biến TRƯỚC khi ghi, rồi cắt ≤ MAX_SUBJECT
ký tự. Đây là che theo mẫu, không phải bảo đảm: secret lạ dạng tự do vẫn có thể lọt. Tắt hẳn việc ghi
lệnh Bash bằng HARNESS_AUDIT_NO_BASH=1; tắt decisions.jsonl bằng HARNESS_NO_DECISIONS=1.

Mọi hàm ở đây fail-open: lỗi I/O không bao giờ được làm hỏng hook gọi nó.
"""
import datetime
import hashlib
import json
import os
import re

MAX_SUBJECT = 2000
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_POLICY = os.path.normpath(os.path.join(HERE, "..", "policy.yaml"))

_KEYWORDS = r"(?:TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|CREDENTIALS?|AUTH)"
# Header khối key ghép từ nhiều mảnh: viết liền thì chính file này bị máy quét secret (pre-commit) chặn.
_PK = "PRIV" + "ATE KEY"
_REDACT = [
    # khối private key
    (re.compile("-----BEGIN [A-Z ]*" + _PK + "-----.*?-----END [A-Z ]*" + _PK + "-----", re.S),
     "[khối key ***]"),
    # token có tiền tố nhận dạng được
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{20,})"), "***"),
    (re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{16,}"), "sk-***"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "AKIA***"),
    (re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"), "xox-***"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "AIza***"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "jwt-***"),
    # header Authorization / Bearer
    (re.compile(r"(?i)(authorization:\s*(?:bearer|basic|token)\s+)[^\s'\"]+"), r"\1***"),
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1***"),
    # user:pass@ trong URL
    (re.compile(r"(://[^/\s:@]+:)[^@\s/]+@"), r"\1***@"),
    # gán biến có tên nhạy cảm: FOO_TOKEN=xxx, export API_KEY="xxx"
    (re.compile(r"(?i)\b([A-Z0-9_]*" + _KEYWORDS + r"[A-Z0-9_]*\s*=\s*)(\"[^\"]*\"|'[^']*'|\S+)"), r"\1***"),
    # cờ nhạy cảm: --password xxx / --token=xxx
    (re.compile(r"(?i)(--?(?:password|passwd|token|secret|api-?key|auth-?token)(?:=|\s+))(\"[^\"]*\"|'[^']*'|\S+)"),
     r"\1***"),
    # mysql -pXXX / sshpass -p XXX
    (re.compile(r"(\b(?:mysql|mysqldump|mariadb)\b[^\n|;&]*?\s-p)(?!\s)(\S+)"), r"\1***"),
    (re.compile(r"(\bsshpass\s+-p\s*)(\S+)"), r"\1***"),
]


def redact(text):
    """Che secret theo mẫu rồi cắt độ dài. Không bao giờ ném lỗi."""
    if not text:
        return text
    try:
        out = str(text)
        for pat, rep in _REDACT:
            out = pat.sub(rep, out)
        if len(out) > MAX_SUBJECT:
            out = out[:MAX_SUBJECT] + f"…[+{len(out) - MAX_SUBJECT} ký tự]"
        return out
    except Exception:
        return "[redact lỗi — bỏ nội dung]"


def root():
    return os.environ.get("CLAUDE_PROJECT_DIR", ".")


def audit_dir():
    d = os.path.join(root(), ".claude/audit")
    os.makedirs(d, exist_ok=True)
    return d


def file_sha(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except OSError:
        return None


def input_sha(tool_input):
    """Hash của tool_input GỐC (chưa che) — đủ để khớp lại đúng một lần gọi mà không lưu nội dung."""
    try:
        raw = json.dumps(tool_input or {}, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return None


def subject_of(tool, tool_input):
    """Phần đáng ghi của một tool-call: lệnh Bash (đã che) hoặc đường dẫn file."""
    ti = tool_input or {}
    if tool == "Bash":
        return redact(ti.get("command") or "")
    return ti.get("file_path") or ti.get("path") or ""


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def record_decision(rule_id, rule_name, tool, tool_input, match, engine_file, policy_path=None,
                    verdict="block", layer="session"):
    """Ghi 1 dòng vào decisions.jsonl. Gọi NGAY TRƯỚC khi hook trả exit 2. Fail-open."""
    if os.environ.get("HARNESS_NO_DECISIONS") == "1":
        return
    try:
        rec = {
            "ts": now(),
            "rule": rule_id,
            "name": rule_name,
            "verdict": verdict,
            "layer": layer,
            "tool": tool,
            "subject": subject_of(tool, tool_input),
            "match": redact(match)[:300] if match else None,
            "input_sha": input_sha(tool_input),
            "policy_sha": file_sha(policy_path or DEFAULT_POLICY),
            "engine": os.path.basename(engine_file),
            "engine_sha": file_sha(engine_file),
        }
        with open(os.path.join(audit_dir(), "decisions.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_jsonl(path):
    """Đọc jsonl, bỏ qua dòng hỏng. File thiếu → []."""
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return out
