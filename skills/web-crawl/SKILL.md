---
name: web-crawl
description: >-
  Crawl/scrape a website or single page into clean LLM-ready MARKDOWN. Use when the user wants to
  fetch a URL's content, scrape a site, extract an article/page as text, pull docs from the web
  into the wiki, or "crawl this link". Markdown (not raw HTML) = 5-10x fewer tokens. Default
  backend uses Moli (Rust headless engine, ~30MB RAM, JS-rendered markdown, zero API key) with
  automatic fallback to builtin urllib→markdown; premium backends (Firecrawl/Crawl4AI/Jina) are a
  one-config adapter.
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: utils
  requires:
    harness: ">=1.3.127"
    bin: [python3]
    scripts: [~/.claude/skills/web-crawl/scripts/web-crawl.py]
---

# Skill: web-crawl

Fetch a web page and turn it into clean markdown for the wiki / an LLM. Backend is a quarantined
adapter (`harness/web-crawl.config.yaml`, `verified:false`) — the builtin works now, no key.

## WHAT

### Purpose và context
- **Purpose:** turn a URL (or a site) into clean markdown and land it in `raw/` or a wiki draft, never raw HTML.
- **Trigger (when to use):**
  - User gives a URL and wants its content ("crawl this", "scrape", "fetch the page", "đọc trang này").
  - Pulling external docs/articles into `raw/` or a wiki draft.
  - Bulk reading many pages for research (prefer a premium backend then).
- **Non-goals:** not cloning a page's UI/look (that is `/web-clone`); not writing straight into `wiki/` (goes via `/propose` / `ingest`); not crawling auth-walled or disallowed content.

### Mental model
`URL → backend (Moli Rust headless default · WebFetch in-session · builtin urllib+regex fallback · premium adapter firecrawl/crawl4ai/jina) → markdown → raw/ or wiki draft → /propose or ingest → wiki`.

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | URL | có | page or site to fetch; or a local `.html` file for `md` mode |
| In | `--out` path | không | where to save; convention `raw/<slug>.md` |
| In | premium backend config | không | `backend` + `api_key_env`/`endpoint` + `verified:true` in `harness/web-crawl.config.yaml` |
| Out | markdown file | có | clean text in `raw/` or a wiki draft |
| Out | backend disclosure | có | which backend produced it (`moli`, `builtin`, or premium) |

### Rules và capabilities
- RULE-01 (MUST): Markdown, not raw HTML — that is the point (token savings + clean text).
- RULE-02 (MUST): Respect robots.txt / site Terms; do not crawl auth-walled or disallowed content.
- RULE-03 (MUST): Default to **Moli** (`moli fetch "<URL>" --dump markdown --wait domstable --timeout-ms 15000` or via `web-crawl.py fetch`) for fast, ~30MB RAM headless JS-rendered extraction. Fall back to `builtin` urllib only when `moli` is unavailable.
- RULE-04 (MUST): Self-test: `python3 ~/.claude/skills/web-crawl/scripts/web-crawl.py --self-test`.
- Capabilities: headless JS-rendered fetch via Moli (`~/.local/bin/moli`); fallback HTTP fetch + HTML→markdown conversion; write to `raw/` or wiki draft only.

### Failure boundaries
- Site is JS-rendered and neither `moli` nor in-session WebFetch is available → **partial** (builtin has no JS render).
- Whole-site crawl requested without a wired premium backend or batch loop → run a bash/python loop over `moli fetch <url> --dump markdown` for known URL lists (10–100 URLs), or wire Firecrawl/Crawl4AI for recursive site discovery.
- robots.txt / Terms disallow or page is auth-walled → **blocked**, do not crawl (use **Orca Browser** if human login/2FA is required).
- Fetch error → **failed**, report URL + error.

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | effect | URL | Fast headless JS-rendered fetch via Moli: `web-crawl.py fetch "<URL>" --out raw/<slug>.md` (or direct `moli fetch "<URL>" --dump markdown --wait domstable --timeout-ms 15000`) | `raw/<slug>.md` | `moli` missing → auto-falls back to builtin urllib (W02) |
| W02 | judgment | URL, session type | Fallback when `moli` absent: in-session WebFetch tool (B01) or builtin `urllib` (`backend: builtin`) | `raw/<slug>.md` | whole-site discovery needed → W03 |
| W03 | effect | config | Recursive whole-site discovery → wire premium backend in `harness/web-crawl.config.yaml`, flip `verified:true` (B02) | premium output | not wired → report limit, do not claim |
| W04 | effect | markdown | Land in `raw/` or wiki draft, then `/propose` / `ingest` | file saved | never into `wiki/` directly |

Chi tiết từng bước (nguồn chân lý cho W01–W04):

1. **Mặc định (1 trang hoặc batch 10–100 URLs, có render JS, ~30MB RAM, không cần API key):**
   Dùng `web-crawl.py fetch` (tự gọi `moli` dưới nền) hoặc gọi trực tiếp `moli`:
   ```bash
   python3 ~/.claude/skills/web-crawl/scripts/web-crawl.py fetch "<URL>" --out raw/<slug>.md
   # hoặc gọi trực tiếp Moli CLI:
   moli fetch "<URL>" --dump markdown --wait domstable --timeout-ms 15000 > raw/<slug>.md
   ```
2. **Fallback offline / không có `moli`:**
   Nếu máy chưa cài `moli`, `web-crawl.py` tự động rơi về `builtin` (`urllib` + regex HTML→markdown, không render JS) hoặc dùng tool **WebFetch** có sẵn trong phiên. Nếu đã có file HTML local: `web-crawl.py md <file.html>`.
3. **Crawl đệ quy toàn site (auto-discover link):** cấu hình `backend: firecrawl|crawl4ai|jina` + `api_key_env`/`endpoint` trong `harness/web-crawl.config.yaml`, bật `verified:true`. Nếu đã có danh sách URL, chỉ cần vòng lặp gọi `moli fetch`.
4. **Lưu kết quả:** ghi markdown vào `raw/` hoặc wiki draft, sau đó dùng `/propose` / `ingest` để đưa vào wiki.

### Branches
| ID | Kind | Guard | Hành vi | Skip / failure | Rejoin |
|---|---|---|---|---|---|
| B01 | capability_optional | running in an agent session with WebFetch, page is JS-heavy | use WebFetch instead of the builtin script | no WebFetch → W02 builtin (no JS render, partial) | W04 |
| B02 | capability_optional | premium backend configured and `verified:true` | crawl via firecrawl/crawl4ai/jina adapter (JS, whole-site) | not wired → stay on builtin, state its limits (RULE-03) | W04 |
| B03 | user_optional | local HTML already downloaded | `web-crawl.py md <file.html>` instead of fetch | — | W04 |

### Validation và stopping
Backend is healthy when `python3 ~/.claude/skills/web-crawl/scripts/web-crawl.py --self-test` passes. Done when the markdown file exists in `raw/` or a draft and the reply names the backend used. Quality of builtin output (extraction, JS content) is review-only, not claimed.

### Examples
- **Positive:** "crawl https://example.com/blog/post into raw" (static page, no key) → `python3 ~/.claude/skills/web-crawl/scripts/web-crawl.py fetch "https://example.com/blog/post" --out raw/example-post.md` → markdown saved, then suggest `ingest`.
- **Boundary/failure:** "scrape the whole docs site" with `verified:false` → builtin is single page only → report that a premium backend must be wired in `harness/web-crawl.config.yaml`; do not claim the site was crawled.

### Reference — Related
- `~/.claude/skills/web-crawl/scripts/web-crawl.py` + `harness/web-crawl.config.yaml` (the backend adapter).
- **Real engines (the upgrade):** Firecrawl (`github.com/mendableai/firecrawl`, managed + MCP),
  Crawl4AI (`github.com/unclecode/crawl4ai`, OSS self-host), Jina Reader. MinerU (in your stars) for PDFs/docs.
- `/web-clone` — when you want the page's UI/look, not its text.
- `build-now-adapt-later` — the quarantine pattern this backend follows.
