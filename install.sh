#!/usr/bin/env bash
# install.sh — cài PoC vendor-neutral harness vào 1 dự án bằng MỘT lệnh (luồng B0–B4).
#
# Usage:
#   bash install.sh [project_root] [--vendor claude,opencode,cursor,codex,kiro] [--no-verify]
#
#   project_root       thư mục dự án đích (mặc định: thư mục hiện tại)
#   --vendor           ép danh sách vendor; bỏ qua → tự DÒ (.claude/ · opencode.json · .cursor/ · .kiro/ · .codex)
#   --no-verify        bỏ bước chạy demo.sh + test-broad.sh
#   --with-wiki        seed khung llmwiki/
#   --with-skills      cài skill đi kèm trong skills/ (offline, SHA256SUMS; SKILLS_LIST=a,b để chọn)
#   --with-knowledgelib  đăng ký MCP KnowledgeLib GLOBAL (~/.claude.json) — 1 kho dùng chung mọi repo.
#                        Path lấy từ env KNOWLEDGELIB_HOME (default ~/Documents/Repo/knowledgelib_data).
#   --with-rtk         bật hook rtk GLOBAL nếu chưa có (rtk init -g --auto-patch; hook là của máy, không per-repo)
#   --full             bật tất cả (--with-wiki --with-skills --with-knowledgelib --with-rtk)
#   --profile NAME     cài hồ sơ ~/.claude từ profiles/NAME (skill, settings, CLAUDE.md) rồi THOÁT, không cài vào dự án.
#                      Kèm được: --private DIR (repo riêng có skills/), --dry-run, --with-moli, --force-docs.
#   --with-statusline  cài thanh usage GLOBAL cho Claude Code + Codex (bin/usage/install.py; không đè statusLine
#                      có sẵn — thay thì chạy tay: python3 bin/usage/install.py install --replace). Không nằm trong --full.
#
# Idempotent. CI + pre-commit luôn cài (sàn đảm bảo); adapter chỉ cài cho vendor có mặt.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # nguồn = poc-vendor-neutral/
ROOT="."; VENDORS=""; VERIFY=1; CLEAN=0; WITH_SKILLS=0; WITH_WIKI=0; WITH_KNOWLEDGELIB=0; WITH_RTK=0; WITH_STATUSLINE=0; GH_HOME=""; PROFILE=""; PROFILE_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --vendor) VENDORS="${2:-}"; shift 2;;
    --no-verify) VERIFY=0; shift;;
    --clean) CLEAN=1; shift;;
    --with-skills) WITH_SKILLS=1; shift;;
    --with-wiki) WITH_WIKI=1; shift;;
    --with-knowledgelib) WITH_KNOWLEDGELIB=1; shift;;
    --with-rtk) WITH_RTK=1; shift;;
    --with-statusline) WITH_STATUSLINE=1; shift;;
    --profile) PROFILE="${2:-}"; shift 2;;
    --private) PROFILE_ARGS+=(--private "${2:-}"); shift 2;;
    --dry-run|--with-moli|--force-docs|--keep-legacy-hooks) PROFILE_ARGS+=("$1"); shift;;
    --full) WITH_SKILLS=1; WITH_WIKI=1; WITH_KNOWLEDGELIB=1; WITH_RTK=1; shift;;   # đủ 4 trụ: harness + skills + llmwiki + knowledgelib
    -*) echo "tham số lạ: $1" >&2; exit 1;;
    *) ROOT="$1"; shift;;
  esac
done
if [ -n "$PROFILE" ]; then
  exec python3 "$SRC/bin/profile.py" install --profile "$PROFILE" ${PROFILE_ARGS[@]+"${PROFILE_ARGS[@]}"}
fi
ROOT="$(cd "$ROOT" && pwd)"
DEST="$ROOT/harness/poc-vendor-neutral"; OUT="$DEST/out"
log(){ printf '\033[1;32m[install]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[install]\033[0m %s\n' "$*"; }
has(){ case ",$VENDORS," in *",$1,"*) return 0;; *) return 1;; esac; }

# --clean: gỡ bản cũ trước khi cài (cài mới sạch). Cần uninstall.sh cạnh script.
if [ "$CLEAN" = 1 ] && [ -f "$SRC/uninstall.sh" ]; then
  log "--clean → gỡ bản cũ trước"
  bash "$SRC/uninstall.sh" "$ROOT" || warn "uninstall gặp lỗi, vẫn cài tiếp"
fi

# ── B0. Copy lõi vào dự án ──
log "B0 · copy lõi → $DEST"
mkdir -p "$DEST/bin"
if [ "$(cd "$SRC" && pwd -P)" != "$(cd "$DEST" && pwd -P)" ]; then
  cp "$SRC/policy.yaml" "$SRC/gen-converters.py" "$SRC/demo.sh" "$SRC/test-broad.sh" "$DEST/"
  cp "$SRC/bin/"*.py "$DEST/bin/"
  for f in install.sh uninstall.sh bootstrap.sh test-rules.sh test-propose.sh test-plan.sh test-codex.sh README.md DOCS.md; do [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DEST/"; done
  [ -d "$SRC/skills" ] && { rm -rf "$DEST/skills"; cp -R "$SRC/skills" "$DEST/skills"; }
else
  log "  · lõi đã ở đúng chỗ (SRC=DEST), bỏ qua copy"
fi
printf 'out/\n' > "$DEST/.gitignore"
# audit log (R4) là dữ liệu phiên local — không để bị commit nhầm vào dự án đích
if ! grep -qxF '.claude/audit/' "$ROOT/.gitignore" 2>/dev/null; then
  printf '.claude/audit/\n' >> "$ROOT/.gitignore"
fi
chmod +x "$DEST/bin/"*.py "$DEST/gen-converters.py" "$DEST"/*.sh 2>/dev/null || true
python3 -c 'import yaml' 2>/dev/null || { warn "thiếu pyyaml → thử pip install"; pip3 install --quiet pyyaml 2>/dev/null || warn "không cài được pyyaml — lõi sẽ fail-open tới khi có pyyaml"; }

# ── B1. Dò vendor ──
if [ -z "$VENDORS" ]; then
  det=""
  [ -d "$ROOT/.claude" ] && det="${det}claude,"
  { [ -f "$ROOT/opencode.json" ] || [ -d "$ROOT/.opencode" ]; } && det="${det}opencode,"
  [ -d "$ROOT/.cursor" ] && det="${det}cursor,"
  { [ -f "$ROOT/AGENTS.md" ] || [ -d "$ROOT/.codex" ]; } && det="${det}codex,"
  [ -d "$ROOT/.kiro" ] && det="${det}kiro,"
  VENDORS="${det%,}"
  # harness chạy TRONG Claude Code → nếu không dò ra vendor nào, mặc định Claude
  # (tạo .claude/settings.json để wire PreToolUse hook, kể cả project chưa có .claude/)
  [ -z "$VENDORS" ] && VENDORS="claude"
fi
log "B1 · vendor: $VENDORS"

# ── B2. Sinh wiring từ policy ──
log "B2 · gen-converters → out/"
( cd "$DEST" && python3 gen-converters.py >/dev/null )

# ── B3. Cắm wiring ──
log "B3 · cắm wiring"
# CI (sàn, luôn cài)
mkdir -p "$ROOT/.github/workflows"
cp "$OUT/ci/harness.yml" "$ROOT/.github/workflows/harness.yml"
log "  ✓ CI       → .github/workflows/harness.yml"
# pre-commit (sàn)
PC="$ROOT/.pre-commit-config.yaml"
if [ ! -f "$PC" ]; then
  cat > "$PC" <<'YML'
repos:
  - repo: local
    hooks:
      - id: llmwiki-harness
        name: llmwiki harness validator (layer=repo)
        entry: python3 harness/poc-vendor-neutral/bin/llmwiki-validate.py files
        language: system
        files: '\.md$'
YML
  log "  ✓ pre-commit → .pre-commit-config.yaml (tạo mới)"
elif grep -q 'llmwiki-harness' "$PC"; then
  log "  · pre-commit → đã có hook llmwiki-harness, bỏ qua"
else
  warn "  pre-commit đã tồn tại → thêm tay khối repo:local id=llmwiki-harness (xem out/pre-commit-snippet.yaml)"
fi
# Claude (merge hooks vào settings.json)
if has claude; then
  python3 - "$ROOT" "$OUT/claude/settings.snippet.json" <<'PY'
import json,os,sys,shutil
root,snip=sys.argv[1],sys.argv[2]
sp=os.path.join(root,'.claude','settings.json')
os.makedirs(os.path.dirname(sp),exist_ok=True)
cur=json.load(open(sp,encoding='utf-8')) if os.path.exists(sp) else {}
if os.path.exists(sp): shutil.copy(sp, sp+'.bak')
add=json.load(open(snip,encoding='utf-8'))
MARK='harness/poc-vendor-neutral/bin/'
cur.setdefault('hooks',{})
# 1) GỠ mọi hook harness cũ trước (idempotent kể cả khi đổi format lệnh → không trùng);
#    giữ nguyên hook KHÁC của user trong cùng event.
for ev,defs in list(cur['hooks'].items()):
    nd=[]
    for d in defs:
        d['hooks']=[h for h in (d.get('hooks') or []) if MARK not in (h.get('command') or '')]
        if d.get('hooks'): nd.append(d)
    if nd: cur['hooks'][ev]=nd
    else: cur['hooks'].pop(ev,None)
# 2) THÊM hook harness mới (đúng 1 bản, đã fail-open)
for ev,entries in add.get('hooks',{}).items():
    cur['hooks'].setdefault(ev,[]).extend(entries)
json.dump(cur,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('  \033[1;32m✓\033[0m Claude   → .claude/settings.json (merged, backup .bak)')
PY
fi
# KnowledgeLib (R19) — đăng ký MCP server GLOBAL (~/.claude.json), dùng chung MỌI repo,
# không phải per-project. Idempotent: đã có thì bỏ qua, không đè.
if [ "$WITH_KNOWLEDGELIB" = 1 ] && has claude; then
  KL_HOME="${KNOWLEDGELIB_HOME:-$HOME/Documents/Repo/knowledgelib_data}"
  if [ -f "$KL_HOME/src/mcp_server.py" ]; then
    python3 - "$KL_HOME" <<'PY'
import json,os,sys,shutil
kl_home=sys.argv[1]
cp=os.path.expanduser('~/.claude.json')
cur=json.load(open(cp,encoding='utf-8')) if os.path.exists(cp) else {}
cur.setdefault('mcpServers',{})
if 'knowledgelib' in cur['mcpServers']:
    print('  · KnowledgeLib → ~/.claude.json đã có mcpServers.knowledgelib, bỏ qua')
else:
    if os.path.exists(cp): shutil.copy(cp, cp+'.bak')
    cur['mcpServers']['knowledgelib']={
        'command':'python3',
        'args':[os.path.join(kl_home,'src','mcp_server.py')],
        'env':{'KNOWLEDGELIB_PATH':kl_home},
    }
    json.dump(cur,open(cp,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print('  \033[1;32m✓\033[0m KnowledgeLib → ~/.claude.json (mcpServers.knowledgelib, global, backup .bak)')
PY
  else
    warn "  KnowledgeLib → $KL_HOME/src/mcp_server.py không tồn tại, bỏ qua (chỉnh KNOWLEDGELIB_HOME nếu path khác)"
  fi
  # Skill `knowledgelib` — nguồn là SKILL.md ở gốc repo KnowledgeLib (không nằm trong bộ skill ngoài).
  # Layout giống `npx skills`: bản thật ở ~/.agents/skills, symlink từ ~/.claude/skills.
  # Idempotent: đã có thì KHÔNG đè (bản đang dùng có thể do bạn chỉnh); lệch bản chỉ báo.
  if [ -f "$KL_HOME/SKILL.md" ]; then
    SK_DST="$HOME/.agents/skills/knowledgelib"; SK_LINK="$HOME/.claude/skills/knowledgelib"
    if [ -f "$SK_DST/SKILL.md" ]; then
      if cmp -s "$KL_HOME/SKILL.md" "$SK_DST/SKILL.md"; then log "  · skill knowledgelib đã có, khớp bản trong repo"
      else warn "  skill knowledgelib đã có nhưng LỆCH bản trong repo — giữ nguyên (cập nhật tay: cp $KL_HOME/SKILL.md $SK_DST/SKILL.md)"; fi
    else
      mkdir -p "$SK_DST" && cp "$KL_HOME/SKILL.md" "$SK_DST/SKILL.md" && log "  ✓ skill knowledgelib → $SK_DST"
    fi
    if [ ! -e "$SK_LINK" ] && [ ! -L "$SK_LINK" ]; then
      mkdir -p "$HOME/.claude/skills" && ln -s "../../.agents/skills/knowledgelib" "$SK_LINK" && log "  ✓ symlink $SK_LINK"
    fi
  else
    warn "  skill knowledgelib: không thấy $KL_HOME/SKILL.md, bỏ qua"
  fi
fi
# opencode (permission.edit native — merge tự động)
if has opencode; then
  python3 - "$ROOT" "$OUT/opencode/opencode.json" <<'PY'
import json,os,sys,shutil
root,snip=sys.argv[1],sys.argv[2]
op=os.path.join(root,'opencode.json')
cur=json.load(open(op,encoding='utf-8')) if os.path.exists(op) else {}
if os.path.exists(op): shutil.copy(op,op+'.bak')
add=json.load(open(snip,encoding='utf-8'))
perm=cur.get('permission')
if not isinstance(perm,dict): perm={}
edit=perm.get('edit')
if not isinstance(edit,dict): edit={}
for k,v in add.get('permission',{}).get('edit',{}).items():
    if k=='*': edit.setdefault(k,v)     # giữ default của user nếu đã có
    else: edit[k]=v                      # luôn áp glob deny của harness
perm['edit']=edit; cur['permission']=perm
cur.setdefault('$schema', add.get('$schema','https://opencode.ai/config.json'))
json.dump(cur,open(op,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('  \033[1;32m✓\033[0m opencode → opencode.json (merged permission.edit, backup .bak)')
PY
fi
# advisory (nhắc — dựa CI là chính)
if has cursor; then mkdir -p "$ROOT/.cursor/rules"; cp "$OUT/cursor/.cursor/rules/harness.mdc" "$ROOT/.cursor/rules/"; log "  ✓ Cursor   → .cursor/rules/harness.mdc (advisory)"; fi
if has kiro;   then mkdir -p "$ROOT/.kiro/steering"; cp "$OUT/kiro/.kiro/steering/harness.md" "$ROOT/.kiro/steering/"; log "  ✓ Kiro     → .kiro/steering/harness.md (advisory)"; fi
if has codex; then
  python3 "$DEST/gen-converters.py" --merge-codex-hooks "$ROOT/.codex/hooks.json" "$OUT/codex/hooks.json"
  log "  ✓ Codex    → .codex/hooks.json (R20, R22)"
  warn "  Codex: duyệt (trust) hook qua /hooks trước khi hook chạy."
fi

# ── B4. Verify ──
if [ "$VERIFY" = 1 ]; then
  log "B4 · verify"
  if bash "$DEST/demo.sh" >/dev/null 2>&1; then log "  ✓ demo.sh"; else warn "  demo.sh FAIL — kiểm pyyaml"; fi
  if bash "$DEST/test-broad.sh" >/dev/null 2>&1; then log "  ✓ test-broad.sh"; else warn "  test-broad.sh FAIL"; fi
fi

# ── (tùy chọn) trụ 3: seed khung llmwiki (nhanh, idempotent — không đè file có sẵn) ──
if [ "$WITH_WIKI" = 1 ]; then
  log "+ seed khung llmwiki"
  mkdir -p "$ROOT/llmwiki/raw" "$ROOT/llmwiki/wiki/concepts" "$ROOT/llmwiki/wiki/entities" "$ROOT/llmwiki/wiki/sources/adr" "$ROOT/llmwiki/wiki/sources/draft"
  [ -f "$ROOT/llmwiki/wiki/index.md" ] || printf '# Wiki index\n\n| File | Type | Date |\n|---|---|---|\n' > "$ROOT/llmwiki/wiki/index.md"
  [ -f "$ROOT/llmwiki/wiki/log.md" ]   || printf '# Log\n' > "$ROOT/llmwiki/wiki/log.md"
  log "  ✓ llmwiki/ (wiki/{concepts,entities,sources/draft} · raw/ · index.md · log.md)"
  # tài liệu hướng dẫn overstack — TRAVEL cùng khung xương (luôn refresh bản mới nhất)
  if [ -z "${REPO_RAW:-}" ]; then
    # Opt-in: không tự tải/chạy mã từ mạng. Đặt REPO_RAW=<url raw nguồn tin cậy của bạn> để bật.
    log "  · bỏ qua tải overstack.html/templates/global harness (đặt REPO_RAW=<raw url> để bật)"
  elif command -v curl >/dev/null 2>&1; then
    mkdir -p "$ROOT/llmwiki/html"
    if curl -fsSL "$REPO_RAW/llmwiki/html/overstack.html" -o "$ROOT/llmwiki/html/overstack.html" 2>/dev/null; then
      log "  ✓ llmwiki/html/overstack.html (tài liệu overstack — mở bằng trình duyệt)"
    else
      warn "  overstack.html chưa tải được (mạng?) → lấy tay: $REPO_RAW/llmwiki/html/overstack.html"
    fi
    # foundation.yaml — nguồn mục "Nền tảng" (GH#6): seed CHỈ khi chưa có, không đè bản đã điền
    if [ ! -f "$ROOT/harness/foundation.yaml" ]; then
      mkdir -p "$ROOT/harness"
      if curl -fsSL "$REPO_RAW/harness/templates/foundation-template.yaml" -o "$ROOT/harness/foundation.yaml" 2>/dev/null; then
        log "  ✓ harness/foundation.yaml (nguồn mục Nền tảng — điền rồi regen overstack.html; medic probe foundation gác drift)"
      else
        warn "  foundation-template chưa tải được (mạng?) — điền tay: $REPO_RAW/harness/templates/foundation-template.yaml"
      fi
    fi
    # sổ cây vấn đề (problem-tree) — seed CHỈ khi chưa có, không bao giờ ghi đè sổ đang dùng
    if [ ! -f "$ROOT/llmwiki/html/problem-tree.html" ] && [ ! -f "$ROOT/llmwiki/html/fdk-problem-tree.html" ]; then
      if curl -fsSL "$REPO_RAW/harness/templates/problem-tree-template.html" -o "$ROOT/llmwiki/html/problem-tree.html" 2>/dev/null; then
        log "  ✓ llmwiki/html/problem-tree.html (sổ cây vấn đề — hook R17 tự xả sổ khi phiên kết thúc)"
      else
        warn "  problem-tree template chưa tải được (mạng?) — hook R17 sẽ fail-open tới khi có sổ"
      fi
    fi
    # v4 ĐẢO GH#51 (council-038, GH#63 Phase 2): engine KHÔNG travel vào repo nữa — GLOBAL-SHARED
    # ~/.claude/harness là source-of-truth (U10). Repo chỉ giữ llmwiki (data) + .harness-stamp.
    # Hooks fire từ GLOBAL ~/.claude/settings.json (install-harness --global wire, guard theo stamp).
    GH_HOME="${OVERSTACK_HARNESS_HOME:-$HOME/.claude/harness}"
    # 1) đảm bảo global harness có mặt VÀ KHÔNG CŨ.
    #    Trước đây chỉ cài khi VẮNG → re-curl bootstrap không bao giờ refresh global → global kẹt
    #    ở bản cũ mãi mãi. Hệ quả dây chuyền: stamp dự án == global (cùng bản cũ) → hook
    #    harness-integrity thấy bằng nhau → im lặng → DỰ ÁN KHÔNG BAO GIỜ BIẾT CÓ NĂNG LỰC MỚI,
    #    dù framework đã bump. Đây là mắt xích đứt duy nhất của chuỗi "model biết mình có gì mới".
    #    Nay: vắng HOẶC version remote khác version đang cài → cài lại (idempotent).
    GH_CUR=""; GH_NEW=""
    [ -f "$GH_HOME/version.json" ] && GH_CUR="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version',''))" "$GH_HOME/version.json" 2>/dev/null || echo "")"
    if [ -f "$SRC/../version.json" ]; then
      GH_NEW="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version',''))" "$SRC/../version.json" 2>/dev/null || echo "")"
    else
      VJ="$(mktemp)"
      curl -fsSL "$REPO_RAW/harness/version.json" -o "$VJ" 2>/dev/null \
        && GH_NEW="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version',''))" "$VJ" 2>/dev/null || echo "")"
      rm -f "$VJ"
    fi
    if [ ! -f "$GH_HOME/version.json" ] || { [ -n "$GH_NEW" ] && [ "$GH_CUR" != "$GH_NEW" ]; }; then
      if [ -f "$GH_HOME/version.json" ]; then
        log "  global harness CŨ (v${GH_CUR:-?} → v$GH_NEW) → cập nhật install-harness.sh --global"
      else
        log "  global harness chưa có ($GH_HOME) → cài install-harness.sh --global"
      fi
      IH="$SRC/../scripts/install-harness.sh"
      if [ ! -f "$IH" ]; then
        IH="$(mktemp)"
        curl -fsSL "$REPO_RAW/harness/scripts/install-harness.sh" -o "$IH" 2>/dev/null || IH=""
      fi
      if [ -n "$IH" ] && [ -f "$IH" ]; then
        bash "$IH" --global || warn "  cài global lỗi — chạy tay: install-harness.sh --global (fail-open, không chặn install)"
      else
        warn "  không tải được install-harness.sh (mạng?) — cài tay: $REPO_RAW/harness/scripts/install-harness.sh --global"
      fi
    fi
    # 2) stamp — hợp đồng travel "repo này được gác bản vX" (session_start so với global → warn skew, U11)
    TV="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version','0'))" "$GH_HOME/version.json" 2>/dev/null || echo 0)"
    printf '{"schema": 1, "guarded_by": "%s"}\n' "${TV:-0}" > "$ROOT/llmwiki/.harness-stamp"
    log "  ✓ llmwiki/.harness-stamp (guarded_by: ${TV:-0})"
    # 3) U10: gỡ engine bản GH#51 từng copy vào repo (fdk/tools, harness/scripts) — global thay thế.
    #    KHÔNG đụng repo framework (nhận diện: có fdk/wiki — framework_only, downstream không có).
    if [ ! -d "$ROOT/fdk/wiki" ]; then
      for d in fdk/tools harness/scripts; do
        if [ -d "$ROOT/$d" ]; then rm -rf "$ROOT/${d:?}" && log "  ✓ gỡ $d khỏi repo (engine dùng bản global — U10)"; fi
      done
      rmdir "$ROOT/fdk" 2>/dev/null || true
    fi
  fi
fi

# ── (tùy chọn) cài skill (GLOBAL — khác phạm vi với harness theo-project) ──
# Skill đi kèm repo này ($SRC/skills/<tên>/) — TỰ ĐỦ, cài offline, không cần mạng/npx/nguồn ngoài.
# Nguồn gốc + giấy phép từng skill: skills/NOTICE.md. Toàn vẹn: skills/SHA256SUMS (kiểm trước khi cài).
# Mặc định cài hết; SKILLS_LIST="a,b" để chọn.
if [ "$WITH_SKILLS" = 1 ]; then
  SK_SRC="$SRC/skills"
  if [ -d "$SK_SRC" ]; then
    SK_ALL="$(cd "$SK_SRC" && for d in */; do [ -f "$d/SKILL.md" ] && printf '%s,' "${d%/}"; done)"
    SKILLS_LIST="${SKILLS_LIST:-${SK_ALL%,}}"
    if [ -f "$SK_SRC/SHA256SUMS" ]; then
      if (cd "$SK_SRC" && shasum -a 256 -c SHA256SUMS >/dev/null 2>&1); then log "  ✓ skills/SHA256SUMS khớp"
      else warn "  skills/SHA256SUMS LỆCH — file trong skills/ đã bị sửa so với bản phát hành; kiểm git diff trước khi dùng"; fi
    fi
    log "+ cài skill vendored (global): $SKILLS_LIST"
    IFS=',' read -r -a _SK <<< "$SKILLS_LIST"
    for n in "${_SK[@]}"; do
      [ -f "$SK_SRC/$n/SKILL.md" ] || { warn "  skill '$n' không có trong $SK_SRC — bỏ qua"; continue; }
      dst="$HOME/.agents/skills/$n"; lnk="$HOME/.claude/skills/$n"
      if [ -f "$dst/SKILL.md" ]; then
        if diff -rq "$SK_SRC/$n" "$dst" >/dev/null 2>&1; then log "  · $n đã có, khớp"
        else warn "  $n đã có nhưng LỆCH bản trong repo — giữ nguyên (cập nhật tay: cp -R $SK_SRC/$n/. $dst/)"; fi
      else
        mkdir -p "$dst" && cp -R "$SK_SRC/$n/." "$dst/" && log "  ✓ $n → $dst"
      fi
      if [ ! -e "$lnk" ] && [ ! -L "$lnk" ]; then
        mkdir -p "$HOME/.claude/skills" && ln -s "../../.agents/skills/$n" "$lnk"
      fi
    done
  else
    warn "  không thấy $SK_SRC — bỏ qua skill vendored"
  fi
fi

# ── rtk (Rust Token Killer) — KHÔNG phải skill, là CLI proxy + hook rewrite ──────────────
# Hook rtk là cấu hình GLOBAL của máy (~/.claude/settings.json) — không có hook per-repo:
# `rtk init` không -g chỉ nhét ~5KB chỉ dẫn vào CLAUDE.md dự án (trùng CLAUDE.md.template + RTK.md global).
# Nên repo mới nhận quy ước prefix rtk qua CLAUDE.md.template; --with-rtk chỉ đảm bảo hook máy có mặt.
if command -v rtk >/dev/null 2>&1; then
  RTK_V="$(rtk --version 2>/dev/null | awk '{print $2}')"
  if rtk init --show 2>/dev/null | grep -q '^\[ok\] Hook'; then
    log "  ✓ rtk $RTK_V · hook global đã có"
  elif [ "$WITH_RTK" = 1 ]; then
    log "  + rtk $RTK_V · cài hook global (rtk init -g --auto-patch)"
    rtk init -g --auto-patch 2>&1 | tail -3 | sed 's/^/    /' || warn "  rtk init -g lỗi — chạy tay"
  else
    warn "  rtk $RTK_V có nhưng hook global CHƯA cấu hình → thêm --with-rtk (hoặc chạy: rtk init -g)"
  fi
else
  warn "  chưa có rtk — CLAUDE.md.template yêu cầu prefix rtk; cài rồi chạy: install.sh --with-rtk"
fi

# ── thanh usage (statusline) Claude Code + Codex — GLOBAL, opt-in, không thuộc --full ──────
if [ "$WITH_STATUSLINE" = 1 ]; then
  log "+ thanh usage (bin/usage/install.py install)"
  python3 "$SRC/bin/usage/install.py" install 2>&1 | sed 's/^/    /' || warn "  cài thanh usage lỗi — chạy tay: python3 $SRC/bin/usage/install.py install"
fi

# ── BẢN ĐỒ NĂNG LỰC CHO MODEL (ADR-005) — mắt xích cuối, đừng bỏ ──────────────────────
# Hook orientation (session_start.py) nói với agent "dự án này có CAPABILITIES.md — bản đồ
# skill/tool đang có". Nhưng nếu KHÔNG AI SINH file đó, hook chẳng có gì để khoe và agent vào
# dự án KHÔNG BIẾT mình có đồ nghề gì → cài xong mà model vẫn mù. Sinh ngay tại đây, từ skill
# global + policy vừa cài. fail-open: bản harness cũ chưa có tool này thì bỏ qua, không chặn.
BC="${GH_HOME:+$GH_HOME/hooks/build-capabilities.py}"
if [ -n "$BC" ] && [ -f "$BC" ]; then
  if python3 "$BC" --root "$ROOT" >/dev/null 2>&1; then
    log "  ✓ CAPABILITIES.md (bản đồ đồ nghề — agent đọc để biết dự án này CÓ GÌ)"
  else
    warn "  không sinh được CAPABILITIES.md — chạy tay: python3 $BC --root ."
  fi
fi

echo ""
log    "═══════════ TRẠNG THÁI 4 TRỤ ═══════════"
log    "  1. Harness      ✓ cài/cập nhật   (per-project: hook validate + CI + 6 rule: R4,R8,R19,R20,R21,R22)"
if [ "$WITH_SKILLS" = 1 ]; then
  log  "  2. Skills       ✓ cài/cập nhật   (GLOBAL ~/.claude/skills; offline, có kiểm SHA256SUMS)"
else
  warn "  2. Skills       — BỎ QUA         → thêm cờ --with-skills (hoặc --full)"
fi
if [ "$WITH_WIKI" = 1 ]; then
  log  "  3. llmwiki      ✓ seed khung     (llmwiki/wiki + raw + index/log)"
else
  warn "  3. llmwiki      — BỎ QUA         → thêm cờ --with-wiki (hoặc --full)"
fi
if [ "$WITH_KNOWLEDGELIB" = 1 ]; then
  log  "  4. KnowledgeLib ✓ nối (R19–R21)  (GLOBAL ~/.claude.json, On-Demand RAG, dùng chung mọi repo)"
else
  warn "  4. KnowledgeLib — BỎ QUA         → thêm cờ --with-knowledgelib (hoặc --full)"
fi

if [ "$WITH_SKILLS" = 0 ] || [ "$WITH_WIKI" = 0 ] || [ "$WITH_KNOWLEDGELIB" = 0 ]; then
  warn "  ► Muốn CẢ 4 trụ trong 1 lệnh: chạy lại với  --full"
fi
log    "═════════════════════════════════════════"
echo "   • Claude: mở session mới (hoặc /hooks reload) để hook có hiệu lực."
echo "   • CI chạy khi push lên GitHub. Sửa luật: harness/poc-vendor-neutral/policy.yaml → chạy lại install.sh (hoặc gen-converters.py)."
