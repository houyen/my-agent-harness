@RTK.md

# Communication Style

Caveman mode ALWAYS ON. Every session, every response. Invoke `/caveman` skill at session start automatically. Never revert unless user says "stop caveman" or "normal mode".

# Git Security & Secret Protection Protocol
- NEVER stage or commit `.env*`, `*.pem`, `*.key`, `*token*`, `*credential*`, `service-account*.json`, or API keys/bot tokens.
- NEVER run `git add .`, `git add -A`, or `git commit -a`. Always stage specific files explicitly: `git add <file>`.
- NEVER bypass git hooks with `git commit --no-verify`.
- Check `git status` and `git diff --cached --stat` before committing.

# Browser Policy (personal repos by default)
- Scope: this policy applies to personal repos, which is the default. A repo is a WORK repo only when its own `CLAUDE.md` or `AGENTS.md` contains the line `Browser policy: work`. Never infer this from the repo name, path or contents; when unsure, treat it as personal.
- WORK repos: Playwright, Chrome headless and the repo's own browser-automation tooling are allowed and expected (E2E, visual QA, screenshots). Browser-based skills that are off by default may be enabled for that repo in its `.claude/settings.json` `skillOverrides`. Still never use the system default browser (`open <url>`), never type passwords or 2FA codes, and leave logins to the user.
- PERSONAL repos (reason: small scale, and Playwright runs burn the personal account's token budget): the rules below apply.
- Whenever a task needs a browser (opening a page, UI/E2E testing, screenshots, verifying a running app, OAuth/verification links), use the **Orca built-in browser** via the `orca` CLI (`orca tab create --url ...`, `orca goto`, `orca snapshot`, `orca screenshot`; see the `orca-cli` skill).
- NEVER use the system default browser: no `open <url>`, `open -a "Google Chrome" <url>`, `xdg-open`, or `webbrowser.open`.
- NEVER launch any other browser either, even headless or via a library: no `puppeteer`/`puppeteer-core`, `playwright`, `selenium`, `chrome --headless`, `chrome --print-to-pdf`, or `chromium`/Chrome binary started from code or CLI. "Orca only" covers automation too, not just opening pages.
- Exception (harness R22, 3 tiers): (1) **Moli** (`~/.local/bin/moli`, local Rust headless engine, no API key, nothing sent to a third party) for reading pages: `moli fetch <url> --dump markdown --wait domstable`, the `web-crawl` skill's default backend. (2) **browser-use** connected to Moli's local CDP (`moli serve --cdp-port 9222 --layout`) for multi-step autonomous flows. (3) Orca for visual checks, local UI/E2E tests, screenshots, OAuth/2FA. Never use Moli or browser-use to log in, type credentials or OTPs, pay, or submit forms on production sites; those stay with the user in Orca.
- Orca can run page JS: `orca eval` (call app functions, read DOM/computed styles, build a data URL and show it in an `<img>` to inspect it), `orca screenshot`. Try these first; most checks (layout, contrast, exported image content) can be done in-page.
- If Orca genuinely cannot do what the task needs (e.g. set viewport width, capture a real file download, print-to-PDF, emulate print media), STOP, tell the user which capability is missing, and ask before using any alternative. Do not switch tools silently, and say so in the report if a check was skipped.
- Exception: scripts already committed in the repo (e.g. `scripts/capture-ui.ts`) may be run when the user asks for that script by name. Do not write new browser-automation scripts on your own.
- If Orca is not running: `orca open --json`, then retry.
- If a site refuses the embedded browser (e.g. Google sign-in says "This browser or app may not be secure"), do NOT fall back to the system browser automatically. Print the URL for the user to copy and tell them why.
- Never type passwords or 2FA codes into pages for the user; leave login steps to them.
