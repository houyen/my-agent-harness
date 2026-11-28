#!/usr/bin/env bash
# test-install.sh — install.sh --no-hooks: không cắm hook phiên nhưng vẫn cài CI + pre-commit; không cờ thì có hook.
cd "$(dirname "$0")" || exit 1
T=0; F=0
ok(){ T=$((T+1)); printf '  \033[1;32mok\033[0m  %s\n' "$1"; }
bad(){ T=$((T+1)); F=$((F+1)); printf '  \033[1;31mFAIL\033[0m %s\n' "$1"; }
has_hooks(){ python3 - "$1" <<'PY'
import json,sys,os
p=os.path.join(sys.argv[1],'.claude','settings.json')
try: d=json.load(open(p))
except Exception: sys.exit(1)
sys.exit(0 if d.get('hooks') else 1)
PY
}
a=$(mktemp -d); b=$(mktemp -d)
bash install.sh "$a" --vendor claude,codex --no-verify --no-hooks >/dev/null 2>&1
has_hooks "$a" && bad "--no-hooks: vẫn cắm hook Claude" || ok "--no-hooks: không có hook trong .claude/settings.json"
[ -f "$a/.codex/hooks.json" ] && bad "--no-hooks: vẫn tạo .codex/hooks.json" || ok "--no-hooks: không tạo .codex/hooks.json"
[ -f "$a/.github/workflows/harness.yml" ] && ok "--no-hooks: CI vẫn cài" || bad "--no-hooks: thiếu CI"
[ -f "$a/.pre-commit-config.yaml" ] && ok "--no-hooks: pre-commit vẫn cài" || bad "--no-hooks: thiếu pre-commit"
bash install.sh "$b" --vendor claude,codex --no-verify >/dev/null 2>&1
has_hooks "$b" && ok "mặc định: có hook Claude" || bad "mặc định: thiếu hook Claude"
[ -f "$b/.codex/hooks.json" ] && ok "mặc định: có .codex/hooks.json" || bad "mặc định: thiếu .codex/hooks.json"
rm -rf "$a" "$b"
echo; printf 'TỔNG: %d test · %d PASS · %d FAIL\n' "$T" "$((T-F))" "$F"
[ "$F" = 0 ]
