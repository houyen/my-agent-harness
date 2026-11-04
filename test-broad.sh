#!/usr/bin/env bash
# test-broad.sh — bộ test lõi sau khi rút gọn còn 6 rule (R4/R8/R19/R20/R21/R22):
# R20 canonical (path/files/claude-hook), robustness fail-open, R22 browser-guard.
# require_origin biên, files-mode, claude-hook hỏng, và KNOWN GAPS (chứng minh vì sao cần CI).
set -uo pipefail
cd "$(dirname "$0")"
CLI="bin/llmwiki-validate.py"
T=0; P=0; F=0
assert(){ local want="$1" desc="$2" got="$3"; T=$((T+1))
  if [ "$got" = "$want" ]; then P=$((P+1)); printf '  \033[1;32mok\033[0m  %s\n' "$desc"
  else F=$((F+1)); printf '  \033[1;31mNO\033[0m  %s \033[2m(want %s got %s)\033[0m\n' "$desc" "$want" "$got"; fi; }
pm(){ python3 "$CLI" path "$1" >/dev/null 2>&1; }                 # path mode
fl(){ local d="$1"; shift; ( cd "$d" && python3 "$OLDPWD/$CLI" --policy "$OLDPWD/policy.yaml" files "$@" ); }  # files mode, path tương đối
hk(){ printf '%s' "$1" | python3 "$CLI" claude-hook >/dev/null 2>&1; }  # claude-hook mode
# Hook ghi .claude/audit/ dưới CLAUDE_PROJECT_DIR → trỏ vào thư mục tạm, không bẩn repo đang test.
export CLAUDE_PROJECT_DIR="$(mktemp -d)"; trap 'rm -rf "$CLAUDE_PROJECT_DIR"' EXIT

echo "── E. files mode (layer=repo) · R20 ──"
tmp="$(mktemp -d)"; mkdir -p "$tmp/self-docs/engine"
printf '%b' '---\nid: self-docs/engine/good\ncanonical_question: q\naliases: [a]\nentity_type: runbook\ndomain: d\nlast_verified: 2026-09-17\n---\n# g\n\nbody\n' > "$tmp/self-docs/engine/good.md"
printf '# bad no frontmatter\n' > "$tmp/self-docs/engine/bad.md"
printf '# notes\n' > "$tmp/notes.md"
fl "$tmp" "self-docs/engine/good.md" >/dev/null 2>&1;                          assert 0 "repo: self-doc tốt" $?
fl "$tmp" "self-docs/engine/bad.md" >/dev/null 2>&1;                           assert 1 "repo: self-doc thiếu frontmatter fail" $?
fl "$tmp" "self-docs/engine/good.md" self-docs/engine/bad.md >/dev/null 2>&1; assert 1 "repo: lô [tốt,xấu] → fail" $?
fl "$tmp" "notes.md" >/dev/null 2>&1;                                          assert 0 "repo: .md ngoài self-docs không bị soi" $?
fl "$tmp" "self-docs/engine/nope.md" >/dev/null 2>&1;                          assert 0 "repo: file không tồn tại → bỏ qua" $?
rm -rf "$tmp"

echo "── F. claude-hook robustness (fail-open / không áp dụng = 0) ──"
hk '{';                                                              assert 0 "JSON hỏng → fail-open" $?
printf '' | python3 "$CLI" claude-hook >/dev/null 2>&1;             assert 0 "stdin rỗng → fail-open" $?
hk '{"tool_name":"Read","tool_input":{"file_path":"self-docs/x.md"}}'; assert 0 "tool Read (không phải write) → 0" $?
hk '{"tool_name":"Write"}';                                         assert 0 "thiếu tool_input → 0" $?
hk '{"tool_name":"MultiEdit","tool_input":{"file_path":"self-docs/x.md","content":"# x"}}'; assert 2 "MultiEdit→self-docs thiếu frontmatter vẫn chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"src/app.ts","content":"x"}}'; assert 0 "file ngoài self-docs → 0" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/raw/x.md","content":"x"}}'; assert 0 "raw/ không còn bị chặn (R1 đã bỏ)" $?

echo "── G. mode/policy robustness ──"
python3 "$CLI" frobnicate x >/dev/null 2>&1;                        assert 0 "mode lạ → fail-open" $?
python3 "$CLI" --policy /no/such.yaml path self-docs/x.md >/dev/null 2>&1; assert 0 "policy thiếu → fail-open" $?
python3 "$CLI" path "" >/dev/null 2>&1;                             assert 0 "path rỗng → 0" $?
r=$(printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"self-docs/x.md","content":"# x"}}' | python3 "$CLI" claude-hook 2>&1 >/dev/null)
case "$r" in *R20*) assert 0 "thiếu frontmatter báo đúng [R20]" 0;; *) assert 0 "thiếu frontmatter báo đúng [R20]" 1;; esac

# ── J. R20 self_docs_canonical ─────────────────────────────────────────
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/runbook.md","content":"# Runbook\n\nNo frontmatter"}}'; assert 2 "R20: self-docs thiếu frontmatter bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/engine/calc.md","content":"---\nid: self-docs/engine/calc\naliases: [calc]\n---\n# Calc"}}'; assert 2 "R20: self-docs thiếu canonical fields bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/engine/calc.md","content":"---\nid: self-docs/engine/calc\ncanonical_question: How to calculate\naliases: [calc]\nentity_type: invalid_type\ndomain: self-docs > engine\nlast_verified: 2026-09-17\n---\n# Calc"}}'; assert 2 "R20: self-docs entity_type lạ bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/engine/calc.md","content":"---\nid: self-docs/engine/calc\ncanonical_question: How to calculate\naliases: [calc]\nentity_type: runbook\ndomain: self-docs > engine\nlast_verified: 2026-09-17\n---\n"}}'; assert 2 "R20: self-docs body rỗng bị chặn" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/engine/calc.md","content":"---\nid: self-docs/engine/calc\ncanonical_question: How to calculate salary\naliases: [calc salary, engine]\nentity_type: runbook\ndomain: self-docs > engine\nlast_verified: 2026-09-17\n---\n# Calc\n\nValid canonical content."}}'; assert 0 "R20: self-docs đủ chuẩn canonical qua" $?
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/MEMORY_INDEX.md","content":"# Index\nNo frontmatter"}}'; assert 0 "R20: MEMORY_INDEX.md miễn trừ" $?

# ── K. R22 orca_browser_only (harness-events.py browser-guard, block=2) ──
EV="bin/harness-events.py"
bg(){ printf '%s' "$1" | python3 "$EV" browser-guard >/dev/null 2>&1; }
bg '{"tool_name":"Bash","tool_input":{"command":"open https://example.com"}}';                     assert 2 "R22: open <url> bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"open -a \"Google Chrome\" https://x.io"}}';       assert 2 "R22: open -a Chrome bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"open -a Safari"}}';                              assert 2 "R22: open -a Safari bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"open report.html"}}';                            assert 2 "R22: open file.html bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"xdg-open http://localhost:3000"}}';              assert 2 "R22: xdg-open bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"python3 -m webbrowser http://x.io"}}';           assert 2 "R22: python -m webbrowser bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"cd app && npm run dev && open http://localhost:3000"}}'; assert 2 "R22: open sau && bị chặn" $?
bg '{"tool_name":"Bash","tool_input":{"command":"sudo -u me open https://x.io"}}';                assert 0 "R22: wrapper lạ (-u) không đoán, fail-open" $?
bg '{"tool_name":"Bash","tool_input":{"command":"orca tab create --url https://example.com --json"}}'; assert 0 "R22: orca tab create qua" $?
bg '{"tool_name":"Bash","tool_input":{"command":"open ."}}';                                      assert 0 "R22: open thư mục (Finder) qua" $?
bg '{"tool_name":"Bash","tool_input":{"command":"open report.pdf"}}';                             assert 0 "R22: open file pdf qua" $?
bg '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"fix: open https://x.io in orca\""}}'; assert 0 "R22: chuỗi trong commit message không chặn nhầm" $?
bg '{"tool_name":"Bash","tool_input":{"command":"grep xdg-open README.md"}}';                     assert 0 "R22: grep xdg-open (đối số) qua" $?
bg '{"tool_name":"Write","tool_input":{"file_path":"a.md","content":"open https://x.io"}}';        assert 0 "R22: tool không phải Bash qua" $?
bg 'not json';                                                                                     assert 0 "R22: stdin hỏng fail-open" $?
HARNESS_ALLOW_SYSTEM_BROWSER=1 bg '{"tool_name":"Bash","tool_input":{"command":"open https://example.com"}}'; assert 0 "R22: env mở khoá tạm" $?

# ── L. decisions.jsonl (bằng chứng mỗi lần chặn) + R4 ghi Bash đã che secret ──
AD="$CLAUDE_PROJECT_DIR/.claude/audit"; rm -rf "$AD"
bg '{"tool_name":"Bash","tool_input":{"command":"cd x && open https://example.com"}}'
hk '{"tool_name":"Write","tool_input":{"file_path":"self-docs/x.md","content":"# x"}}'
n=$(wc -l < "$AD/decisions.jsonl" 2>/dev/null | tr -d ' ');            assert 2 "decisions: 2 lần chặn → 2 dòng" "${n:-0}"
r=$(python3 -c 'import json,sys; d=[json.loads(l) for l in open(sys.argv[1])]; print(d[0]["rule"], d[0]["match"], d[1]["rule"], d[1]["subject"], all(x["input_sha"] and x["policy_sha"] and x["engine_sha"] for x in d))' "$AD/decisions.jsonl")
assert "R22 open https://example.com R20 self-docs/x.md True" "decisions: rule + đoạn khớp + hash đủ" "$r"
bg '{"tool_name":"Bash","tool_input":{"command":"orca tab create --url https://x.io"}}'
hk '{"tool_name":"Write","tool_input":{"file_path":"src/a.ts","content":"x"}}'
n=$(wc -l < "$AD/decisions.jsonl" | tr -d ' ');                        assert 2 "decisions: lệnh được qua không ghi" "$n"
HARNESS_NO_DECISIONS=1 bg '{"tool_name":"Bash","tool_input":{"command":"open https://x.io"}}'; assert 2 "HARNESS_NO_DECISIONS vẫn chặn" $?
n=$(wc -l < "$AD/decisions.jsonl" | tr -d ' ');                        assert 2 "HARNESS_NO_DECISIONS=1 không ghi" "$n"
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"GITHUB_TOKEN=ghp_aaaaaaaaaaaaaaaaaaaaaaaa gh api x --token=zz && curl https://u:pw@h.io -H \"Authorization: Bearer abcdefghij\" && mkdir -p a/b"}}' | python3 "$EV" audit
c=$(tail -1 "$AD/audit.jsonl")
case "$c" in *ghp_a*|*:pw@*|*abcdefghij*|*=zz*) assert 0 "R4: secret trong lệnh Bash bị che" 1;; *) assert 0 "R4: secret trong lệnh Bash bị che" 0;; esac
case "$c" in *"mkdir -p a/b"*) assert 0 "R4: phần không nhạy cảm giữ nguyên" 0;; *) assert 0 "R4: phần không nhạy cảm giữ nguyên" 1;; esac
HARNESS_AUDIT_NO_BASH=1 sh -c "printf '%s' '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"ls\"}}' | python3 $EV audit"
n=$(grep -c '"cmd": "ls"' "$AD/audit.jsonl");                          assert 0 "HARNESS_AUDIT_NO_BASH=1 không ghi lệnh" "$n"
grep -q "## Bị chặn (2 lần" "$AD/log.md" && g=1 || g=0;                 assert 1 "log.md có mục Bị chặn" $g

echo
printf '\033[1mTỔNG: %d test · %d PASS · %d FAIL\033[0m\n' "$T" "$P" "$F"
[ "$F" = 0 ] || exit 1
