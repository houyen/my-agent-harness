# my-agent-harness

Personal Minimal Viable Agent Harness. Vendor-neutral: 1 policy.yaml → gen-converters.py sinh wiring cho Claude / opencode / Cursor / Codex / Kiro / CI / pre-commit.

Nguồn gốc: trích từ một harness tham khảo, verify lại standalone 2026-09-17 (demo.sh 13/13, test-broad.sh 74/74 PASS).

## Cài vào 1 dự án bất kỳ

```bash
git clone --depth 1 https://github.com/houyen/my-agent-harness.git /tmp/my-agent-harness
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

Sửa `policy.yaml` (R1–R22) → chạy lại `python3 gen-converters.py` (sinh `out/`) hoặc chạy lại `install.sh` (tự gen + cắm).

## Browser policy (R22)

- **R22 orca-browser-only**: hook `PreToolUse` (Bash) chặn (exit 2) lệnh mở trình duyệt mặc định của hệ thống — `open <url|*.html>`, `open -a <browser>`, `xdg-open`, `python -m webbrowser`, `osascript ... open location` — và nhắc dùng browser của Orca (`orca tab create --url ...`). Site chặn browser nhúng (vd Google sign-in) thì in URL cho user tự dán, không tự mở Chrome. Mở khoá tạm: `HARNESS_ALLOW_SYSTEM_BROWSER=1`. Chỉ soi token đầu mỗi đoạn shell nên không chặn nhầm commit message; `sudo -u ... open` là gap đã biết (fail-open).

## Rule code theo ngôn ngữ (rules-pull)

Bộ rule code (Go, JS/TS...) lưu trong knowledgelib dạng KU `software/coding-rules/<lang>-code-rules.md`; harness kéo về từng repo:

```bash
python3 bin/rules-pull.py --lang js-ts,go --root /path/to/repo [--kl ~/Documents/Repo/knowledgelib_data]
python3 bin/rules-pull.py --lang go --diff     # xem KU đã đổi gì so với rules.lock, không ghi
python3 bin/rules-pull.py --lang go --check    # exit 1 nếu repo lệch KU (dùng cho CI)
python3 bin/rules-pull.py --lang go --wire-claude   # thêm @docs/rules/go.md vào CLAUDE.md
```

- Sinh `docs/rules/<js|go>.md` (không sửa tay) + `rules.lock` (version + hash từng rule → update luôn có diff).
- `rules.local.yaml` (repo tự viết, pull không ghi đè): `overrides: [{id, action: disable|severity, severity, reason}]`. **`reason` bắt buộc.**
- Chưa sinh config lint (eslint/golangci) từ dữ liệu — mới sinh tài liệu; bước sau.
- Test: `bash test-rules.sh`.

## KnowledgeLib & Self-Docs (R19–R21)

KnowledgeLib KHÔNG phải add-on riêng từng repo — là **1 kho tri thức DUY NHẤT dùng chung mọi repo** bạn làm việc, đăng ký GLOBAL ở `~/.claude.json` (`mcpServers.knowledgelib`), không phải project-scoped `.mcp.json`. Cài bằng `--with-knowledgelib` (hoặc `--full`):

```bash
KNOWLEDGELIB_HOME=/path/to/knowledgelib_data bash install.sh /path/to/project --with-knowledgelib
```

Mặc định `KNOWLEDGELIB_HOME=~/Documents/Repo/knowledgelib_data`. Idempotent — đã có entry thì bỏ qua, không đè.

- **R19 knowledgelib-nudge**: hook `UserPromptSubmit` nhắc agent tra KnowledgeLib khi cần kiến thức domain.
- **R20 self-docs-canonical**: gác cổng ghi file `self-docs/*.md` bắt buộc tuân thủ 6 trường YAML Frontmatter chuẩn (`id`, `canonical_question`, `aliases`, `entity_type`, `domain`, `last_verified`) và body không rỗng.
- **R21 self-docs-sync**: hook `Stop` tự động sanitize (khử PII/tên công ty) và đẩy tài liệu `self-docs/` về kho KnowledgeLib tập trung, đồng thời rebuild Memory Index. Có thể chạy tay bằng `python3 bin/sync-to-knowledgelib.py`.

**Nguyên tắc kiến trúc — On-Demand RAG vs Working Memory:**
- **Zero Eager Context Ingestion**: Tuyệt đối KHÔNG nạp toàn bộ KnowledgeLib hay mục lục index vào context của agent lúc bắt đầu phiên. Context của agent chỉ dành cho Working Memory của dự án hiện tại (`CLAUDE.md`, context task), tránh ô nhiễm ngữ cảnh và cạn token budget khi kho tri thức phình to.
- **Pull on-demand (RAG)**: Agent giữ context sạch; chỉ gọi MCP tool `knowledgelib_search` khi gặp câu hỏi domain-knowledge đã được index.
- Dữ liệu trả về chỉ làm **nền tảng và tham khảo**; AI chủ động đối chiếu và bổ sung thêm kiến thức hiện đại, chuyên sâu của AI để tối ưu câu trả lời.


**Di chuyển lên server nhà sau này:** chỉ sửa 1 chỗ — entry `mcpServers.knowledgelib` trong `~/.claude.json` (đổi `command`/`args`/`env` sang cách trỏ tới server mới) — không đụng project nào khác, vì mọi repo đều trỏ chung 1 entry global này.

## Test

```bash
bash demo.sh          # 13 case nhanh
bash test-broad.sh    # 80 case đầy đủ (bao gồm R20 canonical)
```


## Không mang theo (đặc thù dự án gốc, không vendor-neutral)

- `harness/validators/*.py` (proposal_complete.py, decision_adr.py, no_ai_attribution.py, patterns_guard.py, report_show_path.py) — bản production siết hơn declarative rule ở đây, KHÔNG copy sang vì gắn với llmwiki layout riêng của repo đó.
- `~/.claude/harness` global engine + `install-harness.sh --global` — cơ chế global-shared riêng của bootstrap cũ (GH#51/council-038), không cần cho bộ minimal này.
- Skill llmwiki (`npx skills add <owner>/<repo>#<ref> --global`) — cài riêng, không phải phần của harness. `install.sh --with-skills` cần đặt `SKILLS_REF` tường minh.

## Tuỳ chọn tải từ mạng (opt-in, mặc định TẮT)
Không có gì tự tải/chạy mã từ xa. Chỉ bật khi bạn tự đặt env, trỏ tới nguồn bạn tin cậy:
- `REPO_RAW=<raw url>` — `install.sh --with-wiki` tải overstack.html/templates và có thể chạy `install-harness.sh --global` từ nguồn đó.
- `SKILLS_REF=<owner>/<repo>#<ref>` — `install.sh --with-skills`.
- `HARNESS_REMOTE_POLICY=<raw url policy.yaml>` — hook đầu phiên so policy với bản gốc.

## License
MIT — dùng, sửa, phân phối lại, kể cả biến thành sản phẩm của riêng bạn. Xem [LICENSE](LICENSE).
