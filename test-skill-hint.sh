#!/usr/bin/env bash
# Test bin/skill-hint.py: khớp có dấu/không dấu, bỏ qua lệnh /, cooldown, tối đa 2 gợi ý,
# lỗi/JSON hỏng thì im lặng rc 0, và mọi skill trong skill-hints.json có thật.
set -uo pipefail
cd "$(dirname "$0")"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/hint-test.XXXXXX")"; trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home"; mkdir -p "$HOME"
export SKILL_HINT_STATE="$TMP/state.json"
PASS=0; FAIL=0
ok(){ if eval "$2"; then PASS=$((PASS+1)); echo "  ok  $1"; else FAIL=$((FAIL+1)); echo "  NO  $1"; fi; }
run(){ printf '{"prompt":"%s","session_id":"%s"}' "$1" "${2:-s1}" | python3 bin/skill-hint.py; }

o="$(run 'tôi muốn viết spec cho tính năng mới')"
ok "khớp có dấu → to-spec" '[[ "$o" == *"/to-spec"* ]]'
o="$(run 'toi can viet spec cho tinh nang' s2)"
ok "khớp không dấu" '[[ "$o" == *"/to-spec"* ]]'
o="$(run '/plan viết spec' s3)"
ok "lệnh bắt đầu bằng / thì im" '[ -z "$o" ]'
o="$(run 'xin chào bạn' s4)"
ok "không khớp thì im" '[ -z "$o" ]'
o="$(run 'bug' s5)"
ok "prompt quá ngắn thì im" '[ -z "$o" ]'
o="$(run 'debugging the thing thoroughly please' s6)"
ok "không khớp giữa từ (debugging ≠ bug)" '[ -z "$o" ]'
run 'bị lỗi khi build dự án này' s7 >/dev/null
o="$(run 'bị lỗi khi build dự án này' s7)"
ok "cooldown: lần ngay sau không lặp" '[ -z "$o" ]'
o="$(run 'review code rồi viết spec và chia ticket cho tôi' s8)"
ok "tối đa 2 gợi ý" '[ "$(grep -c "^- /" <<<"$o")" -le 2 ] && [ "$(grep -c "^- /" <<<"$o")" -ge 1 ]'
o="$(printf 'khong phai json' | python3 bin/skill-hint.py)"; rc=$?
ok "JSON hỏng: rc 0, im" '[ "$rc" -eq 0 ] && [ -z "$o" ]'
o="$(SKILL_HINTS_FILE="$TMP/khong-co.json" run 'viết spec cho tôi nhé' s9)"; rc=$?
ok "thiếu file hints: rc 0, im" '[ "$rc" -eq 0 ] && [ -z "$o" ]'
o="$(SKILL_HINT_OFF=1 run 'viết spec cho tôi nhé' s10)"
ok "SKILL_HINT_OFF=1 tắt hẳn" '[ -z "$o" ]'
ok "log không chứa nội dung prompt" '! grep -q "tính năng" "$HOME/.claude/skill-hint.log" && [ -s "$HOME/.claude/skill-hint.log" ]'
ok "mọi skill trong hints có thật" 'python3 - <<PY
import json,sys
from pathlib import Path
h=json.load(open("profiles/personal/skill-hints.json"))
spec=json.load(open("profiles/personal/skills.json"))
known={p.name for p in Path("skills").iterdir() if (p/"SKILL.md").is_file()}|set(spec["private"])|set(spec["external"])
bad=[k for k in h if not k.startswith("_") and k not in known]
sys.exit(1 if bad else 0)
PY'
echo; echo "TỔNG: $((PASS+FAIL)) test · $PASS PASS · $FAIL FAIL"
[ "$FAIL" -eq 0 ]
