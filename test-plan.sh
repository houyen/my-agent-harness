#!/usr/bin/env bash
# test-plan.sh — test cho bin/harness-plan.py (xem trước hệ quả đổi luật) và bin/harness-replay.py
# (chạy engine ứng viên trên audit thật để đo lệnh cũ giờ bị chặn). Fixture tạm, không đụng dự án thật.
set -uo pipefail
cd "$(dirname "$0")"
SRC="$(pwd)"
T=0; P=0; F=0
assert(){ local want="$1" desc="$2" got="$3"; T=$((T+1))
  if [ "$got" = "$want" ]; then P=$((P+1)); printf '  \033[1;32mok\033[0m  %s\n' "$desc"
  else F=$((F+1)); printf '  \033[1;31mNO\033[0m  %s \033[2m(want %s got %s)\033[0m\n' "$desc" "$want" "$got"; fi; }
has(){ grep -qF -- "$2" <<<"$1" && echo 1 || echo 0; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export CLAUDE_PROJECT_DIR="$TMP/none"

# harness giả: một repo git chứa policy + gen-converters + bin, commit làm mốc HEAD
H="$TMP/h"; mkdir -p "$H"
cp "$SRC/policy.yaml" "$SRC/gen-converters.py" "$H/"; cp -R "$SRC/bin" "$H/bin"; rm -rf "$H/bin/__pycache__"
( cd "$H" && git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm base )
PLAN="python3 $H/bin/harness-plan.py --no-replay"
edit(){ python3 - "$H/policy.yaml" "$1" "$2" <<'PY'
import sys; p, a, b = sys.argv[1:]; s = open(p, encoding="utf-8").read()
assert a in s, a; open(p, "w", encoding="utf-8").write(s.replace(a, b, 1))
PY
}
reset(){ ( cd "$H" && git checkout -q -- . ); }

echo "── A. plan: không đổi gì ──"
out=$($PLAN 2>&1);                                                    assert 0 "plan chạy" $?
assert 1 "không có thay đổi luật" "$(has "$out" "(không có)")"
assert 1 "risk low" "$(has "$out" "risk_score: low")"
[ -e "$H/out" ] && g=1 || g=0;                                       assert 0 "plan không ghi out/ thật" $g

echo "── B. plan: phân loại rủi ro ──"
edit '      - "self-docs/*.md"' '      - "self-docs/*.md"
      - "docs/**/*.md"'
out=$($PLAN 2>&1)
assert 1 "thêm target_glob R20 → high CHẶT hơn" "$(has "$out" "[high  ] R20: target_globs CHẶT hơn (+docs/**/*.md)")"
$PLAN --fail-on high >/dev/null 2>&1;                                 assert 1 "--fail-on high → exit 1" $?
reset
edit 'statement: "Đầu phiên' 'statement: "Mở phiên'
out=$($PLAN 2>&1)
assert 1 "chỉ đổi lời văn → low" "$(has "$out" "risk_score: low")"
$PLAN --fail-on medium >/dev/null 2>&1;                               assert 0 "low không vượt --fail-on medium" $?
reset
edit '    matcher: Bash
    timeout: 10
    handler: "harness-events.py browser-guard' '    matcher: Bash
    timeout: 10
    blocking_note: x
    handler: "harness-events.py browser-guard'
edit '    blocking: true' '    blocking: false'
out=$($PLAN 2>&1)
assert 1 "R22 blocking true → false → medium (bỏ lớp chặn)" "$(has "$out" "[medium] R22: blocking true → false")"
reset
python3 - "$H/policy.yaml" <<'PY'
import sys, yaml; p = sys.argv[1]; d = yaml.safe_load(open(p))
d["rules"]["new_repo_rule"] = {"id": "R30", "name": "x", "kind": "require_frontmatter",
                                "enforce_at": ["repo"], "target_globs": ["a/*.md"], "require_keys": ["id"]}
del d["rules"]["audit_log"]
open(p, "w").write(yaml.safe_dump(d, allow_unicode=True))
PY
out=$($PLAN 2>&1)
assert 1 "luật mới chỉ ở repo → medium" "$(has "$out" "[medium] + R30")"
assert 1 "bỏ luật không chặn → low" "$(has "$out" "[low   ] - R4 audit-log")"
assert 1 "luật: 6 → 6" "$(has "$out" "luật: 6 → 6")"
reset
printf '\n# đổi engine\n' >> "$H/bin/harness-events.py"
out=$($PLAN 2>&1)
assert 1 "đổi engine chứa luật chặn → high, nêu R22" "$(has "$out" "engine bin/harness-events.py đổi → logic của R22")"
reset
out=$(python3 "$H/gen-converters.py" --plan --no-replay 2>&1)
assert 1 "gen-converters.py --plan chuyển sang harness-plan" "$(has "$out" "harness plan · mốc HEAD")"

echo "── C. plan: dự án đã cài ──"
D1="$TMP/p1"; mkdir -p "$D1/harness/poc-vendor-neutral"; cp "$H/policy.yaml" "$D1/harness/poc-vendor-neutral/"
D2="$TMP/p2"; mkdir -p "$D2/harness/poc-vendor-neutral"; printf 'rules: {}\n# sửa tay\n' > "$D2/harness/poc-vendor-neutral/policy.yaml"
edit 'statement: "Đầu phiên' 'statement: "Mở phiên'
out=$($PLAN --projects "$D1" "$D2" 2>&1)
assert 1 "dự án ở mốc → SẼ ĐỔI" "$(has "$out" "$D1: 6 luật · đang ở mốc")"
assert 1 "dự án sửa tay → không khớp lịch sử" "$(has "$out" "$D2: 0 luật · không khớp phiên bản nào")"
assert 1 "dự án sửa tay → cài lại +6 luật, 2 high" "$(has "$out" "cài lại: +6 luật · -0 luật · 0 thay đổi khác · 2 high")"
out=$($PLAN --discover "$TMP" 2>&1)
assert 1 "--discover tìm thấy dự án" "$(has "$out" "$D1:")"
reset

echo "── D. replay ──"
RP="python3 $H/bin/harness-replay.py"
R="$TMP/r"; A="$R/.claude/audit"; mkdir -p "$A" "$R/self-docs"
printf '# không frontmatter\n' > "$R/self-docs/bad.md"
printf '%b' '---\nid: a\ncanonical_question: q\naliases: [a]\nentity_type: runbook\ndomain: d\nlast_verified: 2026-11-04\n---\n# ok\n\nbody\n' > "$R/self-docs/good.md"
cat > "$A/audit.jsonl" <<'J'
{"ts":"t1","tool":"Bash","cmd":"ls -la"}
{"ts":"t2","tool":"Bash","cmd":"cd x && open https://example.com"}
{"ts":"t3","tool":"Write","path":"self-docs/bad.md"}
{"ts":"t4","tool":"Write","path":"self-docs/good.md"}
{"ts":"t5","tool":"Edit","path":"self-docs/gone.md"}
not json
J
printf '%s\n' '{"ts":"t6","rule":"R22","tool":"Bash","subject":"open -a Safari"}' > "$A/decisions.jsonl"
out=$($RP --project "$R" 2>&1);                                        assert 0 "replay chạy" $?
assert 1 "đếm tổng 6 (bỏ dòng hỏng)" "$(has "$out" "tổng                             6")"
assert 1 "2 lệnh cũ giờ bị chặn" "$(has "$out" "MỚI BỊ CHẶN                      2")"
assert 1 "R22 bắt open <url> cũ" "$(has "$out" "R22: 1 lệnh")"
assert 1 "R20 bắt self-docs thiếu frontmatter" "$(has "$out" "R20: 1 lệnh")"
assert 1 "file đã xoá → không đo được" "$(has "$out" "không đo được (file không còn)   1")"
assert 1 "decision cũ vẫn chặn" "$(has "$out" "vẫn chặn                         1")"
assert 1 "in giới hạn của phép đo" "$(has "$out" "nội dung HIỆN TẠI")"
$RP --project "$R" --fail-on-new-blocks >/dev/null 2>&1;              assert 1 "--fail-on-new-blocks → exit 1" $?
python3 - "$H/policy.yaml" "$TMP/no22.yaml" <<'PY'
import sys, yaml; d = yaml.safe_load(open(sys.argv[1])); del d["rules"]["orca_browser_only"]
open(sys.argv[2], "w").write(yaml.safe_dump(d, allow_unicode=True))
PY
out=$($RP --project "$R" --policy "$TMP/no22.yaml" 2>&1)
assert 1 "bỏ R22 → lệnh từng bị chặn giờ được qua" "$(has "$out" "mới được qua                     1")"
python3 - "$H/policy.yaml" "$TMP/unrep.yaml" <<'PY'
import sys, yaml; d = yaml.safe_load(open(sys.argv[1])); d["rules"]["orca_browser_only"]["event_action"] = "x"
open(sys.argv[2], "w").write(yaml.safe_dump(d, allow_unicode=True))
PY
out=$($RP --project "$R" --policy "$TMP/unrep.yaml" 2>&1)
assert 1 "hook chặn chưa khai REPLAYABLE → báo không replay được" "$(has "$out" "không replay được (hook chặn chưa khai REPLAYABLE): R22")"
out=$($RP --project "$TMP/empty" --summary 2>&1)
assert 1 "dự án chưa có audit → báo rõ" "$(has "$out" "chưa có audit")"
mkdir -p "$D1/.claude"; cp -R "$A" "$D1/.claude/audit"; cp -R "$R/self-docs" "$D1/"
edit 'statement: "Đầu phiên' 'statement: "Mở phiên'
out=$(python3 "$H/bin/harness-plan.py" --projects "$D1" 2>&1)
assert 1 "plan nhúng kết quả replay của dự án" "$(has "$out" "2 MỚI BỊ CHẶN")"
reset

echo; printf '\033[1mTỔNG: %d test · %d PASS · %d FAIL\033[0m\n' "$T" "$P" "$F"
[ "$F" -eq 0 ]
