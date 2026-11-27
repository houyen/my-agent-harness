#!/usr/bin/env bash
# Test bin/profile.py trên HOME tạm: cài hai lần (lần hai không đổi gì), check bắt symlink chết,
# override lệch và hook llmwiki cũ; context chạy được.
set -uo pipefail
cd "$(dirname "$0")"
REPO="$PWD"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/profile-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home"; mkdir -p "$HOME/.claude"
PRIV="$TMP/private"
PASS=0; FAIL=0
ok(){ if eval "$2"; then PASS=$((PASS+1)); echo "  ok  $1"; else FAIL=$((FAIL+1)); echo "  NO  $1"; fi; }

# repo riêng giả: đủ mọi skill private trong profile
python3 - "$PRIV" <<'PY'
import json, sys
from pathlib import Path
spec = json.loads(Path("profiles/personal/skills.json").read_text())
for n in spec["private"]:
    d = Path(sys.argv[1]) / "skills" / n
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {n}\ndescription: test {n}\n---\n")
PY
# settings có sẵn: một khoá của user + một hook llmwiki cũ + một hook khác phải giữ
cat > "$HOME/.claude/settings.json" <<'JSON'
{"statusLine": {"type": "command", "command": "echo hi"},
 "hooks": {"SessionStart": [{"hooks": [
   {"type": "command", "command": "if [ -f \"$X/llmwiki/.harness-stamp\" ]; then python3 \"$HOME/.claude/harness/hooks/session_start.py\"; fi"},
   {"type": "command", "command": "echo keep-me"}]}]}}
JSON

out1="$(python3 bin/profile.py install --private "$PRIV" 2>&1)"
ok "lần 1 có thay đổi" '[[ "$out1" == *"link propose"* ]]'
ok "lần 1 gỡ hook cũ" '[[ "$out1" == *"gỡ hook llmwiki cũ"* ]]'
ok "skill public là symlink về repo" '[ "$(readlink "$HOME/.claude/skills/plan")" = "$REPO/skills/plan" ]'
ok "skill riêng là symlink về repo riêng" '[ -L "$HOME/.claude/skills/timeline" ] && [ -f "$HOME/.claude/skills/timeline/SKILL.md" ]'
ok "giữ khoá user statusLine" 'grep -q "echo hi" "$HOME/.claude/settings.json"'
ok "giữ hook khác" 'grep -q "keep-me" "$HOME/.claude/settings.json"'
ok "hết hook llmwiki" '! grep -q "harness-stamp" "$HOME/.claude/settings.json"'
ok "có sao lưu settings" 'ls "$HOME"/.claude/profile-backups/*/settings.json >/dev/null 2>&1'
ok "chép CLAUDE.md" 'cmp -s "$HOME/.claude/CLAUDE.md" profiles/personal/CLAUDE.md'

out2="$(python3 bin/profile.py install --private "$PRIV" 2>&1)"
ok "lần 2 không đổi gì" '[[ "$out2" == *"không có gì thay đổi"* ]]'

python3 bin/profile.py check --private "$PRIV" --json > "$TMP/c0.json"
ok "check sạch không có lỗi skill/settings" '! grep -qE "symlink chết|lệch khoá|chưa link|hook llmwiki" "$TMP/c0.json"'

ln -s "$TMP/khong-co" "$HOME/.claude/skills/dangling"
python3 - <<'PY'
import json, os
p = os.path.join(os.environ["HOME"], ".claude/settings.json")
d = json.load(open(p)); d["skillOverrides"]["propose"] = "on"; json.dump(d, open(p, "w"))
PY
out3="$(python3 bin/profile.py check --private "$PRIV" 2>&1)"; rc3=$?
ok "check rc khác 0" '[ "$rc3" -ne 0 ]'
ok "check báo symlink chết" '[[ "$out3" == *"symlink chết"* ]]'
ok "check báo override lệch" '[[ "$out3" == *"lệch khoá skillOverrides"* ]]'

out4="$(python3 bin/harness-doctor.py --profile personal --private "$PRIV" 2>&1)"
ok "doctor có khối Hồ sơ" '[[ "$out4" == *"── Hồ sơ ──"* && "$out4" == *"symlink chết"* ]]'

out5="$(python3 bin/profile.py install --private "$PRIV" 2>&1)"
ok "install sửa lại được" '[[ "$out5" == *"gỡ symlink chết dangling"* ]] && [ ! -e "$HOME/.claude/skills/dangling" ]'

ctx="$(python3 bin/profile.py context --private "$PRIV" 2>&1)"
ok "context in tổng" '[[ "$ctx" == *"Tổng phần profile nạp đầu phiên"* ]]'

out6="$(bash install.sh --profile personal --private "$PRIV" --dry-run 2>&1)"
ok "install.sh --profile chạy được" '[[ "$out6" == *"không có gì thay đổi"* ]]'

echo; echo "TỔNG: $((PASS+FAIL)) test · $PASS PASS · $FAIL FAIL"
[ "$FAIL" -eq 0 ]
