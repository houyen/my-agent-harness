# my-agent-harness

**Tiếng Việt** · [English](README.en.md)

Personal Minimal Viable Agent Harness. Vendor-neutral: 1 policy.yaml → gen-converters.py sinh wiring cho Claude / opencode / Cursor / Codex / Kiro / CI / pre-commit.

Nguồn gốc: chiết từ harness tham khảo (Claude). Từ 2026-10-15 rút gọn còn 6 rule thật sự có dấu vết dùng (audit log + hook); các rule llmwiki/ADR/proposal/pull-gate đã bỏ vì không repo nào có đối tượng để gác.

## Cài vào 1 dự án bất kỳ

```bash
git clone --depth 1 https://github.com/houyen/my-agent-harness.git /tmp/my-agent-harness
bash /tmp/my-agent-harness/install.sh /path/to/target-project
```

Cờ:

- `--vendor claude,opencode,cursor,codex,kiro` — ép danh sách vendor (mặc định tự dò)
- `--no-verify` — bỏ chạy demo.sh + test-broad.sh sau khi cài
- `--clean` — gỡ bản cũ trước khi cài
- `--with-wiki` — seed khung llmwiki/ (raw/, wiki/..., index.md, log.md). Chỉ là thư mục; hiện KHÔNG còn rule nào gác wiki
- `--with-skills` — cài 10 skill đi kèm trong `skills/` vào `~/.agents/skills` + symlink `~/.claude/skills`. Offline, kiểm `skills/SHA256SUMS`, không cần mạng hay nguồn ngoài. `SKILLS_LIST=a,b` để chọn
- `--with-knowledgelib` — đăng ký MCP KnowledgeLib GLOBAL (xem mục dưới)
- `--with-rtk` — cài hook rtk GLOBAL nếu máy chưa có (`rtk init -g --auto-patch`)
- `--full` — bật tất cả (--with-wiki --with-skills --with-knowledgelib --with-rtk)

## Skill đi kèm (`skills/`)

10 skill đi kèm repo, **cài offline, không phụ thuộc nguồn ngoài**. Nguồn gốc và giấy phép từng cái nằm ở `skills/NOTICE.md`.

| Skill | Việc | Nguồn (giữ nguyên bản quyền) |
|---|---|---|
| `impact-check` | Lập bản đồ nơi gọi / phụ thuộc trước khi sửa code dùng chung | Rheinmir/setup @5c5cca9, MIT |
| `safe-change` | Sửa code dùng chung mà không làm gãy nơi gọi | Rheinmir/setup, MIT |
| `md-to-html` | Render Markdown thành HTML độc lập | Rheinmir/setup, MIT |
| `playwright-verify` | Verify bằng script Playwright `.mjs` | Rheinmir/setup, MIT |
| `skill-provenance` | Ghi nguồn + sha256 cho skill (`scripts/`) | Rheinmir/setup, MIT |
| `web-crawl` | Crawl trang web ra Markdown (`scripts/`) | Rheinmir/setup, MIT |
| `caveman`, `caveman-commit`, `caveman-review` | Giọng nén, commit, review ngắn | JuliusBrussee/caveman v4.0.1, Apache-2.0 |
| `agent-reach` | Tra cứu internet đa nền tảng | Panniantong/Agent-Reach, MIT (cần cài riêng CLI `agent-reach`) |

- `caveman*` chỉ là sở thích cá nhân: cài sẵn nhưng harness không bật mode (`CLAUDE.md.template` không ép).
- `orca-cli` đi kèm ứng dụng Orca; `failure-flywheel` không đi kèm vì đầu ra ghi vào `llmwiki/wiki/` (rule đã bỏ).
- Đã có bản khác trong `~/.agents/skills` thì **không đè**, chỉ báo lệch.
- Bảo trì: sửa file trong `skills/` thì chạy lại `cd skills && find . -type f ! -name SHA256SUMS | sort | sed 's#^\./##' | xargs shasum -a 256 > SHA256SUMS`.

## rtk (tuỳ chọn)

`rtk` không phải skill mà là CLI proxy + hook rewrite lệnh để tiết kiệm token. Hook của rtk là cấu hình **global của máy** (`~/.claude/settings.json`), không có hook theo từng repo.

- Repo mới nhận quy ước "prefix mọi lệnh bằng `rtk`" qua `CLAUDE.md.template`.
- `install.sh` luôn báo trạng thái rtk. Thêm `--with-rtk` (hoặc `--full`) thì nếu máy chưa có hook sẽ chạy `rtk init -g --auto-patch`; đã có thì bỏ qua.
- Không dùng `rtk init` không `-g`: nó chỉ nhét ~5KB chỉ dẫn vào CLAUDE.md dự án, trùng với template và `RTK.md` global.

## Rule đang gác


| ID  | Tên                 | Loại                    | Chặn?               | Việc làm                                                  |
| --- | ------------------- | ----------------------- | ------------------- | --------------------------------------------------------- |
| R4  | audit-log           | hook `PostToolUse`      | không               | Ghi `.claude/audit/audit.jsonl` + `log.md` mỗi Write/Edit/Bash (lệnh Bash đã che secret); mỗi lần chặn ghi `decisions.jsonl` |
| R8  | session-health      | hook `SessionStart`     | không               | Báo số rule + check drift policy                          |
| R19 | knowledgelib-nudge  | hook `UserPromptSubmit` | không               | Nhắc tra `knowledgelib_search` mỗi N prompt               |
| R20 | self-docs-canonical | `require_frontmatter`   | có (session + repo) | `self-docs/*.md` phải có 6 trường canonical + body        |
| R21 | self-docs-sync      | hook `Stop`             | không               | Sanitize + sync self-docs sang KnowledgeLib               |
| R22 | orca-browser-only   | hook `PreToolUse`       | có                  | Cấm mở trình duyệt hệ thống, dùng Orca                    |


## Sửa luật

Sửa `policy.yaml` → chạy lại `python3 gen-converters.py` (sinh `out/`) hoặc chạy lại `install.sh` (tự gen + cắm).

### Xem trước hệ quả trước khi cài (plan → replay)

Ý tưởng mượn từ [open-ontologies](https://github.com/fabio-rovai/open-ontologies): xem trước hệ quả, đo trên dữ liệu thật, có bằng chứng kiểm lại được. Áp vào đây bằng script thuần, không cần reasoner.

```bash
python3 gen-converters.py --plan                        # = bin/harness-plan.py: so working tree với HEAD
python3 bin/harness-plan.py --base v1 --diff            # so với mốc khác, in unified diff của out/
python3 bin/harness-plan.py --discover ~/Documents      # + blast radius trên các dự án đã cài (kèm replay)
python3 bin/harness-plan.py --fail-on high              # exit 1 nếu có thay đổi rủi ro high (dùng cho CI)
python3 bin/harness-replay.py --project /path/to/proj   # chạy engine + policy ứng viên trên audit thật
python3 bin/harness-replay.py --engine /tmp/cand/bin --project P --fail-on-new-blocks
```

- **plan** không ghi `out/` thật: nó sinh wiring của cả mốc lẫn bản đang sửa trong thư mục tạm rồi diff. Mỗi thay đổi được chấm điểm: `high` = có chỗ chặn mới hoặc chặt hơn ở session, hoặc engine của luật đang chặn bị đổi; `medium` = CI có thể đỏ, đổi matcher, hoặc bỏ một lớp chặn; `low` = chỉ đổi lời văn hoặc nới lỏng. Với từng dự án, plan báo policy đang cài nằm ở commit nào, cài lại sẽ thêm hoặc bỏ luật gì, và bao nhiêu lệnh cũ sẽ bị chặn.
- **replay** đọc `audit.jsonl` (lệnh đã cho qua) và `decisions.jsonl` (lệnh đã bị chặn), chạy lại bằng **cùng hàm thuần** mà hook dùng (`llmwiki-validate.evaluate`, `harness-events.REPLAYABLE`), rồi báo: vẫn qua · vẫn chặn · **MỚI BỊ CHẶN** · mới được qua · không đo được. Giới hạn (được in ra ở mỗi lần chạy): Write/Edit được đo trên nội dung *hiện tại* của file; lệnh Bash là bản đã che secret; audit trước 2026-11-04 không có Bash. Thêm một hook chặn mới thì khai hàm kiểm của nó vào `REPLAYABLE` trong `harness-events.py`, nếu không replay sẽ báo luật đó là "không replay được".
- **decisions.jsonl**: mỗi lần chặn ghi rule, đoạn khớp, `input_sha`, `policy_sha` và `engine_sha`, đủ để kiểm lại vì sao bị chặn. Tắt bằng `HARNESS_NO_DECISIONS=1`. Tắt việc ghi lệnh Bash vào audit bằng `HARNESS_AUDIT_NO_BASH=1`. Phần che secret dựa theo mẫu (token có tiền tố, `Authorization`, `user:pass@`, biến `*_TOKEN=`/`*_KEY=`, `--password`, `mysql -p`, khối private key), nên **không bảo đảm** che hết.

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
- `rules.local.md` (repo tự viết, pull không ghi đè): ghi chú riêng của repo (stack, quy ước đặc thù); nối nguyên văn vào cuối `docs/rules/<out>.md` dưới heading `## Ghi chú riêng của repo (rules.local.md)`.
- `rules.lock` theo dõi `local_notes_sha`: sửa hoặc xóa `rules.local.md` làm `--check` báo lệch và `--diff` in `~ rules.local.md`.
- **Verdict theo nguồn luật**: mỗi bộ luật mang một từ khoá. `standard` = áp đúng bộ chuẩn KU. `with_local_overrides` = đã bị `rules.local.yaml` tắt hoặc đổi severity, nên "pass" ở repo này không tương đương "pass" theo chuẩn. Từ khoá này được in khi pull, ghi trong `rules.lock` (`verdict`) và ở đầu `docs/rules/<out>.md`. Rule bị đổi severity được đánh dấu ngay tại dòng của nó.
- Chưa sinh config lint (eslint/golangci) từ dữ liệu — mới sinh tài liệu; bước sau.
- Test: `bash test-rules.sh`.

### Đề xuất rule mới từ repo (rules-propose)

Hàng đợi đề xuất rule từ repo lên KU, duyệt trước khi merge vào knowledgelib:

```bash
# Thêm đề xuất vào rules-proposals/<lang>/<ID>.yaml
python3 bin/rules-propose.py add --lang go --id GO-ERR-05 --severity warn --kind review \
  --statement "..." --evidence "..." --origin "..." [--scope prod,tests] [--root .] [--kl PATH]

# Xem danh sách đề xuất (pending / merged)
python3 bin/rules-propose.py list [--lang go] [--root .]

# Merge đề xuất vào KU (tăng version, cập nhật last_verified; chỉ chạy khi có duyệt)
python3 bin/rules-propose.py merge --lang go --id GO-ERR-05 --approve-by "<tên>" [--patch] [--root .] [--kl PATH]
```

- Test: `bash test-propose.sh`.

## KnowledgeLib & Self-Docs (R19–R21)

KnowledgeLib KHÔNG phải add-on riêng từng repo — là **1 kho tri thức DUY NHẤT dùng chung mọi repo** bạn làm việc, đăng ký GLOBAL ở `~/.claude.json` (`mcpServers.knowledgelib`), không phải project-scoped `.mcp.json`. Cài bằng `--with-knowledgelib` (hoặc `--full`):

```bash
KNOWLEDGELIB_HOME=/path/to/knowledgelib_data bash install.sh /path/to/project --with-knowledgelib
```

Mặc định `KNOWLEDGELIB_HOME=~/Documents/Repo/knowledgelib_data`. Idempotent — đã có entry thì bỏ qua, không đè.

`--with-knowledgelib` còn cài **skill `knowledgelib`** từ `$KNOWLEDGELIB_HOME/SKILL.md` (bản thật ở `~/.agents/skills/knowledgelib`, symlink từ `~/.claude/skills/`). Đã có thì không đè; lệch bản chỉ báo để bạn tự cập nhật.

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
bash demo.sh           # 8 case nhanh (R20 path/hook/files, fail-open, sinh wiring)
bash test-broad.sh     # 47 case (R20 canonical, robustness, R22 browser-guard, decisions.jsonl, che secret)
bash test-plan.sh      # 31 case: harness-plan (chấm rủi ro, dự án đã cài) + harness-replay
bash test-rules.sh     # rules-pull (kể cả verdict standard / with_local_overrides)
bash test-propose.sh   # rules-propose
```

## Không mang theo (đặc thù dự án gốc, không vendor-neutral)

- `~/.claude/harness` global engine + `install-harness.sh --global` — cơ chế global-shared riêng của bootstrap cũ (GH#51/council-038), không cần cho bộ minimal này.

## Tuỳ chọn tải từ mạng (opt-in, mặc định TẮT)

Không có gì tự tải/chạy mã từ xa. Chỉ bật khi bạn tự đặt env, trỏ tới nguồn bạn tin cậy:

- `REPO_RAW=<raw url>` — `install.sh --with-wiki` tải overstack.html/templates và có thể chạy `install-harness.sh --global` từ nguồn đó.
- `HARNESS_REMOTE_POLICY=<raw url policy.yaml>` — hook đầu phiên so policy với bản gốc.

## License

MIT — dùng, sửa, phân phối lại, kể cả biến thành sản phẩm của riêng bạn. Xem [LICENSE](LICENSE).

Ngoại lệ: các skill trong `skills/` giữ giấy phép của tác giả gốc (MIT / Apache-2.0) — xem [skills/NOTICE.md](skills/NOTICE.md).