#!/usr/bin/env bash
# test-usage.sh — test thanh usage (bin/usage/): lõi, vỏ Claude, vỏ Codex (MCP), installer.
# Mọi thứ chạy trong HOME/CODEX_HOME tạm, không đụng cấu hình thật của máy.
set -uo pipefail
cd "$(dirname "$0")"
SRC="$(pwd)"
T=0; P=0; F=0
assert(){ local want="$1" desc="$2" got="$3"; T=$((T+1))
  if [ "$got" = "$want" ]; then P=$((P+1)); printf '  \033[1;32mok\033[0m  %s\n' "$desc"
  else F=$((F+1)); printf '  \033[1;31mNO\033[0m  %s \033[2m(want %s got %s)\033[0m\n' "$desc" "$want" "$got"; fi; }
has(){ grep -qF -- "$2" <<<"$1" && echo 1 || echo 0; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
U="$SRC/bin/usage"
export HOME="$TMP/home" CODEX_HOME="$TMP/home/.codex" AGENT_USAGE_STATE_DIR="$TMP/state"
mkdir -p "$HOME" "$AGENT_USAGE_STATE_DIR"

echo "── A. lõi ──"
out=$(python3 - "$U" <<'PY'
import sys; sys.path.insert(0, sys.argv[1]); import core
r = core.load_rates()
print(core.compact(999), core.compact(1500), core.compact(2_500_000))
print("%.6f" % core.request_cost(r, "gpt-6.2-sol", 200_000, 0, 0, 0))
print("%.6f" % core.request_cost(r, "gpt-6.2-sol", 300_000, 0, 0, 0))
print(core.request_cost(r, "khong-co", 10, 0, 0, 0))
print(core.cost_label(0.5, 0), "|", core.cost_label(0, 2), "|", core.cost_label(0.5, 1))
print(core.render("M", 12.4, None, 0, 0, None))
PY
)
assert 1 "compact 999 / 1.5k / 2.5M" "$(has "$out" "999 1.5k 2.5M")"
assert 1 "giá 200k input gpt-6.2-sol = \$0.4 (dưới ngưỡng 272k)" "$(has "$out" "0.400000")"
assert 1 "vượt 272k → input x2 (300k = \$1.2)" "$(has "$out" "1.200000")"
assert 1 "model chưa có giá → None" "$(has "$out" "None")"
assert 1 "nhãn chi phí: có giá / chưa giá / lẫn" "$(has "$out" '$0.5000 | chưa có giá | $0.5000 + ? (1 req chưa có giá)')"
assert 1 "chưa có lượt → 'lượt: chờ dữ liệu'" "$(has "$out" "M · ctx 12% · lượt: chờ dữ liệu")"

echo "── B. vỏ Claude ──"
CL="python3 $U/claude.py"
pl(){ printf '{"session_id":"s1","model":{"display_name":"Opus"},"cost":{"total_cost_usd":%s},"context_window":{"used_percentage":40,"current_usage":{"input_tokens":%s,"cache_creation_input_tokens":%s,"cache_read_input_tokens":%s,"output_tokens":%s}}}' "$@"; }
out=$(pl 0.10 1000 2000 7000 300 | $CL)
assert 2 "in đúng 2 dòng" "$(printf '%s\n' "$out" | wc -l | tr -d ' ')"
assert 1 "dòng 1: model · ctx · lượt · + · tổng" "$(has "$out" "Opus · ctx 40% · lượt: 10.0k in / 300 out · + \$0.1000 · tổng \$0.1000")"
assert 1 "dòng 2: cache + phiên" "$(has "$out" "cache: read 7.0k · write 2.0k · new 1.0k · hit 70% · 1 req | phiên: 1 req, 70% từ cache")"
out=$(pl 0.25 500 0 9500 100 | $CL)
assert 1 "request 2: delta chi phí = 0.15" "$(has "$out" "+ \$0.1500 · tổng \$0.2500")"
assert 1 "phiên cộng dồn 2 req" "$(has "$out" "phiên: 2 req, 82% từ cache")"
out=$(pl 0.25 500 0 9500 100 | $CL)
assert 1 "payload lặp lại không đếm thêm request" "$(has "$out" "phiên: 2 req")"
assert "usage: –" "payload hỏng → 'usage: –'" "$(echo 'not json' | $CL)"
assert "usage: –" "thiếu current_usage → 'usage: –'" "$(echo '{"session_id":"s2"}' | $CL)"
echo 'not json' | $CL >/dev/null 2>&1;                               assert 0 "payload hỏng vẫn exit 0" $?
mkdir -p "$HOME/.orca/agent-hooks"; printf '#!/bin/sh\ncat > "%s/orca-got"\n' "$TMP" > "$HOME/.orca/agent-hooks/claude-statusline.sh"
chmod +x "$HOME/.orca/agent-hooks/claude-statusline.sh"
pl 0.30 1 0 0 1 | $CL >/dev/null
assert 1 "chuyển payload cho hook Orca" "$(has "$(cat "$TMP/orca-got" 2>/dev/null)" '"session_id":"s1"')"

echo "── C. vỏ Codex (MCP) ──"
TID="11111111-2222-3333-4444-555555555555"
mkdir -p "$CODEX_HOME/sessions/2026/11/27"
LOGF="$CODEX_HOME/sessions/2026/11/27/rollout-2026-11-27T10-00-00-$TID.jsonl"
{
  echo '{"type":"turn_context","payload":{"turn_id":"t1","model":"gpt-6.2-sol"}}'
  echo '{"type":"event_msg","payload":{"type":"task_started","turn_id":"t1"}}'
  echo "{\"type\":\"token_usage_record\",\"payload\":{\"turn_id\":\"t1\",\"thread_id\":\"$TID\",\"response_id\":\"r1\",\"usage\":{\"input_tokens\":100000,\"cached_input_tokens\":80000,\"cache_write_input_tokens\":0,\"output_tokens\":1000}}}"
  echo "{\"type\":\"token_usage_record\",\"payload\":{\"turn_id\":\"t1\",\"thread_id\":\"$TID\",\"response_id\":\"r1\",\"usage\":{\"input_tokens\":100000,\"cached_input_tokens\":80000,\"cache_write_input_tokens\":0,\"output_tokens\":1000}}}"
} > "$LOGF"
mcp(){ python3 "$U/codex_mcp.py"; }
req(){ printf '%s\n' "$@" | mcp; }
READ="{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"resources/read\",\"params\":{\"uri\":\"ui://agent-usage/footer\",\"_meta\":{\"com.openai/codex-statusline-state\":{\"thread\":{\"id\":\"$TID\",\"model\":{\"display_name\":\"GPT-6.2-Sol\",\"reasoning_level\":\"medium\"},\"usage\":{\"context\":{\"used_percentage\":4}}}}}}}"
out=$(req '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' "$READ")
assert 3 "3 reply (notification không trả lời)" "$(printf '%s\n' "$out" | wc -l | tr -d ' ')"
assert 1 "tools/list có statusline entrypoint" "$(has "$out" '"type": "statusline"')"
text=$(printf '%s\n' "$out" | tail -1 | python3 -c 'import sys,json;print(json.loads(json.load(sys.stdin)["result"]["contents"][0]["text"]))')
# 20k new*$2 + 80k read*$0.10 + 1k out*$10 = 0.04+0.008+0.01 = $0.058; response trùng r1 chỉ tính 1 lần
assert 1 "footer: model + effort + ctx + lượt + chi phí" "$(has "$text" "GPT-6.2-Sol medium · ctx 4% · lượt: 100.0k in / 1.0k out · + \$0.0580 · tổng \$0.0580")"
assert 1 "footer dòng 2: cache + phiên" "$(has "$text" "cache: read 80.0k · write 0 · new 20.0k · hit 80% · 1 req | phiên: 1 req, 80% từ cache")"
BAD="{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"resources/read\",\"params\":{\"uri\":\"ui://agent-usage/footer\",\"_meta\":{\"com.openai/codex-statusline-state\":{\"thread\":{\"id\":\"khong-phai-uuid\"}}}}}"
text=$(req "$BAD" | python3 -c 'import sys,json;print(json.loads(json.load(sys.stdin)["result"]["contents"][0]["text"]))')
assert "Codex · lượt: chờ dữ liệu" "thread lạ → chờ dữ liệu" "$text"
out=$(req '{"jsonrpc":"2.0","id":5,"method":"khong/co"}' 'rac')
assert 1 "method lạ → -32601" "$(has "$out" '-32601')"
assert 1 "dòng rác → -32700" "$(has "$out" '-32700')"

echo "── D. installer ──"
I="python3 $U/install.py"
mkdir -p "$HOME/.claude" "$CODEX_HOME"
echo '{"model":"x","statusLine":{"type":"command","command":"/old/line.sh"}}' > "$HOME/.claude/settings.json"
cat > "$CODEX_HOME/config.toml" <<'TOML'
model = "gpt-6.2-sol"

[tui]
status_line_provider = { server = "cache-statusline", tool = "statusline" }
status_line = ["model-with-reasoning", "context-used"]

[tui.model_availability_nux]
"gpt-6.1-sol" = 4
TOML
cp "$CODEX_HOME/config.toml" "$TMP/codex-orig.toml"
out=$($I install 2>&1);                                               assert 0 "install (không --replace) exit 0" $?
assert 1 "giữ statusLine Claude có sẵn" "$(has "$out" "GIỮ NGUYÊN; chạy lại với --replace")"
assert "/old/line.sh" "settings.json không bị đổi" "$(python3 -c 'import json,os;print(json.load(open(os.environ["HOME"]+"/.claude/settings.json"))["statusLine"]["command"])')"
cmp -s "$CODEX_HOME/config.toml" "$TMP/codex-orig.toml"; assert 0 "config.toml không bị đổi khi đã có provider khác" $?
assert 1 "đã chép 4 file vào ~/.agent-usage" "$(ls "$HOME/.agent-usage" | grep -c -e core.py -e claude.py -e codex_mcp.py -e rates.json | grep -q 4 && echo 1 || echo 0)"
out=$($I install --replace 2>&1);                                     assert 0 "install --replace exit 0" $?
assert 1 "Claude statusLine trỏ ~/.agent-usage/claude.py" "$(has "$(cat "$HOME/.claude/settings.json")" "/.agent-usage/claude.py")"
assert "x" "giữ các khoá khác của settings.json" "$(python3 -c 'import json,os;print(json.load(open(os.environ["HOME"]+"/.claude/settings.json"))["model"])')"
python3 -c 'import tomllib,os;tomllib.load(open(os.environ["CODEX_HOME"]+"/config.toml","rb"))'; assert 0 "config.toml sau cài vẫn đúng TOML" $?
v=$(python3 -c 'import tomllib,os;d=tomllib.load(open(os.environ["CODEX_HOME"]+"/config.toml","rb"));print(d["tui"]["status_line_provider"]["server"], "agent-usage" in d["mcp_servers"], d["tui"]["model_availability_nux"]["gpt-6.1-sol"], d["tui"]["status_line"][0])')
assert "agent-usage True 4 model-with-reasoning" "provider + mcp_servers đúng, bảng con và khoá khác còn nguyên" "$v"
cp "$CODEX_HOME/config.toml" "$TMP/after1.toml"; cp "$HOME/.claude/settings.json" "$TMP/after1.json"
$I install --replace >/dev/null 2>&1
cmp -s "$CODEX_HOME/config.toml" "$TMP/after1.toml" && cmp -s "$HOME/.claude/settings.json" "$TMP/after1.json"; assert 0 "cài lại lần 2 không đổi gì (idempotent)" $?
assert 1 "status báo đã cài cả hai" "$(has "$($I status)" "codex : agent-usage")"
$I uninstall >/dev/null 2>&1;                                         assert 0 "uninstall exit 0" $?
assert "/old/line.sh" "uninstall trả lại statusLine Claude cũ" "$(python3 -c 'import json,os;print(json.load(open(os.environ["HOME"]+"/.claude/settings.json"))["statusLine"]["command"])')"
cmp -s "$CODEX_HOME/config.toml" "$TMP/codex-orig.toml"; assert 0 "uninstall trả config.toml về đúng bản gốc" $?
rm -rf "$HOME/.agent-usage" "$HOME/.claude/settings.json"; : > "$CODEX_HOME/config.toml"
$I install >/dev/null 2>&1;                                           assert 0 "máy trống: install exit 0" $?
v=$(python3 -c 'import tomllib,os;d=tomllib.load(open(os.environ["CODEX_HOME"]+"/config.toml","rb"));print(d["tui"]["status_line_provider"]["server"])')
assert "agent-usage" "máy trống: tạo [tui] + provider" "$v"
assert 1 "máy trống: tạo statusLine Claude" "$(has "$(cat "$HOME/.claude/settings.json")" "/.agent-usage/claude.py")"
printf 'model = "x"\n[tui\n' > "$CODEX_HOME/config.toml"; cp "$CODEX_HOME/config.toml" "$TMP/broken.toml"
$I install --only codex >/dev/null 2>&1;                              assert 1 "config.toml hỏng sẵn → exit 1" $?
cmp -s "$CODEX_HOME/config.toml" "$TMP/broken.toml"; assert 0 "config.toml hỏng sẵn → không ghi đè" $?
$I >/dev/null 2>&1;                                                   assert 1 "không lệnh → in hướng dẫn, exit 1" $?

echo; printf '\033[1mTỔNG: %d test · %d PASS · %d FAIL\033[0m\n' "$T" "$P" "$F"
[ "$F" -eq 0 ]
