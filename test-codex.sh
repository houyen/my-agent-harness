#!/usr/bin/env bash
# Exerciser for Codex PreToolUse and generated project wiring.
set -euo pipefail
cd "$(dirname "$0")"
SRC="$PWD"
TMP="$(mktemp -d "$SRC/out-codex-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
ROOT="$TMP/project with spaces"
mkdir -p "$ROOT/.codex" "$ROOT/self-docs" "$ROOT/src"
git -C "$ROOT" init -q
unset HARNESS_ALLOW_SYSTEM_BROWSER
T=0; P=0; F=0
assert(){ local want="$1" desc="$2" got="$3"; T=$((T+1))
  if [ "$got" = "$want" ]; then P=$((P+1)); printf '  \033[1;32mok\033[0m  %s\n' "$desc"
  else F=$((F+1)); printf '  \033[1;31mNO\033[0m  %s \033[2m(want %s got %s)\033[0m\n' "$desc" "$want" "$got"; fi; }

payload(){
  python3 -c 'import json, sys
cwd, tool, key, value = sys.argv[1:]
print(json.dumps(dict(cwd=cwd, session_id="codex-test", tool_name=tool,
                      tool_input={key: json.loads(value) if tool == "Bash" else value})))' "${EVENT_CWD:-$ROOT}" "$@"
}
decision(){
  local name="$1" expected="$2" input="$3" rc=0 got
  shift 3
  printf '%s' "$input" | "$@" >"$TMP/stdout" 2>"$TMP/stderr" || rc=$?
  got=$(python3 - "$TMP/stdout" "$TMP/stderr" "$rc" <<'PY'
import json, pathlib, sys
out, err = (pathlib.Path(path).read_text() for path in sys.argv[1:3])
rc = sys.argv[3]
if rc != "0":
    print(f"exit {rc}: {err}")
elif not out:
    print("fail-open" if "fail-open" in err else "stderr: " + err if err else "allow")
else:
    try:
        hook = json.loads(out)["hookSpecificOutput"]
        assert hook["hookEventName"] == "PreToolUse"
        assert hook["permissionDecision"] == "deny"
        reason = hook["permissionDecisionReason"]
        assert isinstance(reason, str) and reason
        print(reason.split("]", 1)[0] + "]" if reason.startswith("[") else reason)
    except (ValueError, TypeError, KeyError, AssertionError):
        print("JSON deny lỗi: " + out)
PY
)
  assert "$expected" "$name" "$got"
}
check(){
  local name="$1" expected="$2"
  shift 2
  decision "$name" "$expected" "$(payload "$@")" python3 "$SRC/bin/codex-hook.py"
}
patch(){
  local name="$1" expected="$2" key="${3:-patch}"
  check "$name" "$expected" apply_patch "$key" "$(cat)"
}

check 'R22: Bash open URL bị chặn' '[R22]' Bash command '"open https://x.io"'
check 'R22: Bash orca được phép' allow Bash command '"orca tab create --url https://x.io"'
check 'R22: Bash argv open URL bị chặn' '[R22]' Bash command '["open","https://x.io"]'
check 'R22: Bash argv giữ nguyên ranh giới đối số' allow Bash command '["git","commit","-m","test; open https://x.io"]'
check 'R22: Bash argv bash -lc <script> bị chặn' '[R22]' Bash command '["bash","-lc","open https://x.io"]'
check 'R22: Bash argv bash -lc lệnh thường được phép' allow Bash command '["bash","-lc","git status"]'

patch 'R20: Add thiếu frontmatter bị chặn' '[R20]' <<'PATCH'
*** Begin Patch
*** Add File: self-docs/x.md
+# x
*** End Patch
PATCH
cat > "$ROOT/self-docs/x.md" <<'DOC'
---
id: x
canonical_question: q
aliases: [x]
entity_type: runbook
domain: docs
last_verified: 2026-09-17
---
# x
Body.
DOC
{
  printf '%s\n' '*** Begin Patch' '*** Add File: self-docs/good.md'
  sed 's/^/+/' "$ROOT/self-docs/x.md"
  printf '%s\n' '*** End Patch'
} > "$TMP/good.patch"
patch 'R20: Add đủ frontmatter được phép qua tool_input.command' allow command < "$TMP/good.patch"

patch 'R20: Update bỏ frontmatter khỏi file hợp lệ bị chặn' '[R20]' <<'PATCH'
*** Begin Patch
*** Update File: self-docs/x.md
@@
----
-id: x
-canonical_question: q
-aliases: [x]
-entity_type: runbook
-domain: docs
-last_verified: 2026-09-17
----
 # x
*** End Patch
PATCH
patch 'R20: Update nhiều hunk giữ frontmatter được phép' allow <<'PATCH'
*** Begin Patch
*** Update File: self-docs/x.md
@@
-id: x
+id: new-x
@@ # x
-Body.
+New body.
*** End of File
*** End Patch
PATCH
patch 'R20: Add ngoài glob được phép' allow <<'PATCH'
*** Begin Patch
*** Add File: src/x.md
+# x
*** End Patch
PATCH
patch 'R20: Delete được phép' allow <<'PATCH'
*** Begin Patch
*** Delete File: self-docs/x.md
*** End Patch
PATCH
printf '# x\n' > "$ROOT/src/x.md"
patch 'R20: Move vào self-docs kiểm đường đích và nội dung mới' '[R20]' <<'PATCH'
*** Begin Patch
*** Update File: src/x.md
*** Move to: self-docs/moved.md
@@
-# x
+# moved
*** End Patch
PATCH
patch 'R20: Move ra khỏi self-docs dùng đường đích' allow <<'PATCH'
*** Begin Patch
*** Update File: self-docs/x.md
*** Move to: src/moved.md
@@
----
-id: x
-canonical_question: q
-aliases: [x]
-entity_type: runbook
-domain: docs
-last_verified: 2026-09-17
----
 # x
*** End Patch
PATCH
EVENT_CWD="$ROOT/src" patch 'R20: path tương đối với cwd, glob neo ở gốc repo' '[R20]' <<'PATCH'
*** Begin Patch
*** Add File: ../self-docs/from-subdir.md
+# x
*** End Patch
PATCH
decision 'JSON hỏng: fail-open và ghi stderr' fail-open '{' python3 "$SRC/bin/codex-hook.py"
decision 'Payload thiếu cwd: fail-open và ghi stderr' fail-open '{"tool_name":"Bash","tool_input":{}}' python3 "$SRC/bin/codex-hook.py"
patch 'Hunk không khớp: fail-open và ghi stderr' fail-open <<'PATCH'
*** Begin Patch
*** Update File: self-docs/x.md
@@
-impossible line
+updated line
*** End Patch
PATCH
mkdir -p "$TMP/missing-policy/bin"
cp "$SRC/bin/codex-hook.py" "$SRC/bin/llmwiki-validate.py" "$TMP/missing-policy/bin/"
bash_input="$(payload Bash command '"open https://x.io"')"
decision 'Thiếu policy: fail-open và ghi stderr' fail-open "$bash_input" python3 "$TMP/missing-policy/bin/codex-hook.py"

mkdir "$TMP/generator"
cp "$SRC/gen-converters.py" "$SRC/policy.yaml" "$TMP/generator/"
python3 "$TMP/generator/gen-converters.py" >/dev/null
CODEX_JSON="$TMP/generator/out/codex/hooks.json"
wrapper=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hooks"]["PreToolUse"][0]["hooks"][0]["command"])' "$CODEX_JSON")
cd "$ROOT/src"
decision 'Wrapper thiếu script: deny hợp lệ' 'my-agent-harness: thiếu harness/poc-vendor-neutral/bin/codex-hook.py' "$bash_input" sh -c "$wrapper"
cd "$SRC"

config="$ROOT/.codex/hooks.json"
printf '%s\n' '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"echo project-hook"}]}],"SessionStart":[{"hooks":[{"type":"command","command":"echo session-hook"}]}]}}' > "$config"
cp "$config" "$TMP/original.json"
same_hooks(){
  python3 -c 'import json,sys; sys.exit(json.load(open(sys.argv[1])) != json.load(open(sys.argv[2])))' "$@"
}
python3 -c 'import yaml'  # prevent the installer from attempting a dependency install
bash "$SRC/install.sh" "$ROOT" --vendor codex --no-verify > "$TMP/install.log"
assert 0 'Installer nhắc duyệt hook qua /hooks' "$(grep -q 'trust.* /hooks' "$TMP/install.log" && echo 0 || echo 1)"
python3 - "$TMP/original.json" "$CODEX_JSON" "$TMP/expected.json" <<'PY'
import json, sys
_, original, generated, output = sys.argv
expected = json.load(open(original))
expected["hooks"]["PreToolUse"].extend(json.load(open(generated))["hooks"]["PreToolUse"])
with open(output, "w") as stream:
    json.dump(expected, stream)
PY
assert 0 'Install gộp hook mới và giữ hook cũ' "$(same_hooks "$config" "$TMP/expected.json" && echo 0 || echo 1)"
cp "$config" "$TMP/installed.json"
bash "$SRC/install.sh" "$ROOT" --vendor codex --no-verify > "$TMP/install.log"
assert 0 'Install lại không đổi byte nào' "$(cmp -s "$config" "$TMP/installed.json" && echo 0 || echo 1)"
cd "$ROOT/src"
decision 'Wrapper gọi adapter đã cài, kể cả từ thư mục con' '[R22]' "$bash_input" sh -c "$wrapper"
cd "$SRC"
bash "$SRC/uninstall.sh" "$ROOT" > "$TMP/uninstall.log"
assert 0 'Uninstall trả cấu hình hook về như cũ' "$(same_hooks "$config" "$TMP/original.json" && echo 0 || echo 1)"

printf '\n\033[1mTỔNG: %d test · %d PASS · %d FAIL\033[0m\n' "$T" "$P" "$F"
[ "$F" = 0 ]
