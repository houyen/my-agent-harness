# my-agent-harness

Personal Minimal Viable Agent Harness. Vendor-neutral: 1 policy.yaml → gen-converters.py sinh wiring cho Claude / opencode / Cursor / Codex / Kiro / CI / pre-commit.

Nguồn gốc: trích từ `harness/poc-vendor-neutral/` (Payroll CTD, 2026-07-16), verify lại standalone 2026-09-17 (demo.sh 13/13, test-broad.sh 74/74 PASS, không dính path/tên công ty).

## Cài vào 1 dự án bất kỳ

```bash
git clone <this-repo> /tmp/my-agent-harness
bash /tmp/my-agent-harness/install.sh /path/to/target-project
```

Cờ:
- `--vendor claude,opencode,cursor,codex,kiro` — ép danh sách vendor (mặc định tự dò)
- `--no-verify` — bỏ chạy demo.sh + test-broad.sh sau khi cài
- `--clean` — gỡ bản cũ trước khi cài
- `--with-wiki` — seed khung llmwiki/ (raw/, wiki/concepts, entities, sources/draft, index.md, log.md)
- `--with-skills` — cài skill llmwiki (global, qua npx)
- `--with-knowledgelib` — đăng ký MCP KnowledgeLib GLOBAL (xem mục dưới)
- `--full` — bật cả 4 (--with-wiki --with-skills --with-knowledgelib)

## Sửa luật

Sửa `policy.yaml` (R1–R19) → chạy lại `python3 gen-converters.py` (sinh `out/`) hoặc chạy lại `install.sh` (tự gen + cắm).

## KnowledgeLib (R19)

KnowledgeLib KHÔNG phải add-on riêng từng repo — là **1 kho tri thức DUY NHẤT dùng chung mọi repo** bạn làm việc, đăng ký GLOBAL ở `~/.claude.json` (`mcpServers.knowledgelib`), không phải project-scoped `.mcp.json`. Cài bằng `--with-knowledgelib` (hoặc `--full`):

```bash
KNOWLEDGELIB_HOME=/path/to/knowledgelib_data bash install.sh /path/to/project --with-knowledgelib
```

Mặc định `KNOWLEDGELIB_HOME=~/Documents/Repo/knowledgelib_data`. Idempotent — đã có entry thì bỏ qua, không đè.

Rule `R19 knowledgelib-nudge` (hook `UserPromptSubmit`, không chặn, mỗi 5 lượt — chỉnh bằng env `LLMWIKI_KNOWLEDGELIB_GATE_EVERY`) nhắc agent gọi tool MCP `knowledgelib_search` trước khi tự bịa cho câu hỏi domain-knowledge đã có unit trong catalog.

**Di chuyển lên server nhà sau này:** chỉ sửa 1 chỗ — entry `mcpServers.knowledgelib` trong `~/.claude.json` (đổi `command`/`args`/`env` sang cách trỏ tới server mới) — không đụng project nào khác, vì mọi repo đều trỏ chung 1 entry global này.

## Test

```bash
bash demo.sh          # 13 case nhanh
bash test-broad.sh    # 74 case đầy đủ
```

## Không mang theo (đặc thù Payroll CTD, không vendor-neutral)

- `harness/validators/*.py` (proposal_complete.py, decision_adr.py, no_ai_attribution.py, patterns_guard.py, report_show_path.py) — bản production siết hơn declarative rule ở đây, KHÔNG copy sang vì gắn với llmwiki layout riêng của repo đó.
- `~/.claude/harness` global engine + `install-harness.sh --global` — cơ chế global-shared riêng của bootstrap cũ (GH#51/council-038), không cần cho bộ minimal này.
- Skill llmwiki qua `npx skills add rheinmir/setup#orca --global` — cài riêng, không phải phần của harness.

## Origin
- Trích từ `/Users/thaidt/Documents/CTD/Payroll CTD/harness/poc-vendor-neutral/` (harness/foundation.yaml, commit context Payroll CTD)
- Ngày trích: 2026-09-17
