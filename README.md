# my-agent-harness

**English** · [Tiếng Việt](README.vi.md)

A personal, minimal, vendor-neutral agent harness. One `policy.yaml` is the single source of truth; `gen-converters.py` generates the wiring for Claude Code, opencode, Codex, CI and pre-commit.

Origin: distilled from a larger private harness. On 2026-10-15 it was cut down from 22 rules to the 6 that actually leave a trace in use (audit logs and hooks). Rules for llmwiki / ADR / proposals / pull-gates were removed because no repo had anything for them to guard.

> Docs and rule statements in `policy.yaml` are written in Vietnamese. The code, CLI flags and file layout are language-neutral.

## Install into a project

```bash
git clone --depth 1 https://github.com/houyen/my-agent-harness.git /tmp/my-agent-harness
bash /tmp/my-agent-harness/install.sh /path/to/target-project
```

Flags:
- `--vendor claude,opencode,codex`: force the vendor list (default: auto-detect)
- `--no-verify`: skip running demo.sh + test-broad.sh after install
- `--clean`: remove a previous install first
- `--with-wiki`: seed an `llmwiki/` skeleton (raw/, wiki/..., index.md, log.md). Directories only; no rule guards the wiki any more
- `--with-skills`: install the 19 bundled skills in `skills/` into `~/.agents/skills` with symlinks from `~/.claude/skills`. Offline, verified against `skills/SHA256SUMS`, no network or external source. `SKILLS_LIST=a,b` to pick a subset
- `--with-knowledgelib`: register the KnowledgeLib MCP server globally (see below)
- `--with-rtk`: install the global rtk hook if the machine does not have it (`rtk init -g --auto-patch`)
- `--full`: wiki, skills and rtk. KnowledgeLib is **optional** and not part of `--full`; add `--with-knowledgelib` only if you have the store (without it R19 stays silent and R21 does nothing)
- `--with-statusline`: install the GLOBAL usage statusline for Claude Code + Codex (see below; not part of `--full`)

Install is idempotent. CI and pre-commit are always installed (the vendor-neutral floor); per-vendor adapters are installed only for vendors found in the project.

## Bundled skills (`skills/`)

45 skills ship with the repo and install **offline, with no external source**. Origin and license of each are in `skills/NOTICE.md`.

| Skill | Purpose | Source (copyright kept) |
|---|---|---|
| `impact-check` | Map callers/dependents before changing shared code | Rheinmir/setup @5c5cca9, MIT |
| `safe-change` | Modify shared code without breaking callers | Rheinmir/setup, MIT |
| `playwright-verify` | Verify UI via the R22 three tiers (Orca, Moli, browser-use); standalone Playwright only when a repo asks | Rheinmir/setup, MIT |
| `skill-provenance` | Record source + sha256 for skills (`scripts/`) | Rheinmir/setup, MIT |
| `web-crawl` | Crawl a web page to Markdown (`scripts/`) | Rheinmir/setup, MIT |
| `caveman`, `caveman-commit` | Terse voice; commit messages that keep repo trailers and follow the repo's commit language (`caveman-commit` modified) | JuliusBrussee/caveman v4.0.1, Apache-2.0 |
| `propose`, `plan` | Spec before code with an approval stop; execution plan + delegation brief | Rheinmir/setup, MIT (rewritten 2026-11-27) |
| `verify-before-commit` | Run the repo's gate, check staging for secrets, commit message says why | Rheinmir/setup, MIT (rewritten) |
| `orca-issue` | Repro-first incident loop | Rheinmir/setup, MIT (rewritten) |
| `build-now-adapt-later` | Build around an unknown, quarantine it behind one adapter | Rheinmir/setup, MIT (Output Report removed) |
| `wayfinder` | Map a large, foggy chunk of work as decision tickets (GitHub issues or a markdown file) | Rheinmir/setup, MIT (rewritten) |
| `qc-code` | Senior four-part code review + red repro tests | Rheinmir/setup, MIT (rewritten) |
| `graph-mode`, `fable5` | Chat modes: evidence chains; reasoning protocol | Rheinmir/setup, MIT |
| `orca-handover` | Write a seven-part handover file for the next session | Rheinmir/setup, MIT (rewritten) |
| `teach-me` | Explain one thing in seven steps, proven by running it | Rheinmir/setup, MIT (rewritten) |
| `scroll-effects` | Seven vanilla scroll effects | Rheinmir/setup, MIT |
| `next` | Suggests the next skill from the current situation (manual `/next`) | Original to this repo, MIT |
| `blur`, `css-scroll-driven-native`, `dark-mode-maker`, `design-taste-frontend`, `gsap-scrolltrigger-pin`, `infinite-webgl-grid`, `lenis-smooth-scroll`, `mask-reveal-transition`, `redesign-existing-projects`, `svg-stroke-reveal`, `threejs-particle-morph`, `timeline`, `tour-guide` | 13 front-end / motion skills, rewritten from scratch | Original to this repo, MIT (2026-11-28) |

- `caveman*` is a personal preference: installed, but the harness does not switch the mode on (`CLAUDE.md.template` does not force it).
- `orca-cli` ships with the Orca app; `failure-flywheel` is not bundled because it writes into `llmwiki/wiki/` (rules removed).
- An existing copy under `~/.agents/skills` is **never overwritten**, only reported as different.
- Maintenance: after editing files in `skills/`, regenerate checksums with `cd skills && find . -type f ! -name SHA256SUMS ! -path '*/__pycache__/*' ! -name .DS_Store | sort | sed 's#^\./##' | xargs shasum -a 256 > SHA256SUMS`.

## Global profile (`profiles/`)

`bash install.sh --profile personal --private <private-repo>` installs the `~/.claude` profile (skills symlinked to this checkout, `skillOverrides`, CLAUDE.md, legacy llmwiki hooks removed) and exits. Check with `python3 bin/harness-doctor.py --profile personal`. Details and new-machine steps: `profiles/personal/README.md` (Vietnamese). Test: `bash test-profile.sh`.

## rtk (optional)

`rtk` is not a skill: it is a CLI proxy plus a command-rewrite hook that saves tokens. Its hook is **machine-global** configuration (`~/.claude/settings.json`); there is no per-repo hook.

- New repos get the "prefix every command with `rtk`" convention through `CLAUDE.md.template`.
- `install.sh` always reports rtk status. With `--with-rtk` (or `--full`) it runs `rtk init -g --auto-patch` when the machine has no hook, and does nothing if it is already there.
- Avoid plain `rtk init` (no `-g`): it only injects ~5 KB of instructions into the project CLAUDE.md, duplicating the template and the global `RTK.md`.

## Codex adapter

Run `bash install.sh <project_root> --vendor codex` to merge the `PreToolUse` hook into `.codex/hooks.json`. Open `/hooks` in Codex and trust the hook before using it.

The hook applies R22 to Bash commands and checks R20 against the Markdown content that `apply_patch` would produce for paths covered by the policy. Malformed input or a missing policy fails open with a diagnostic on stderr. The wrapper denies if the adapter script is missing.

Run `bash uninstall.sh <project_root>` to remove the harness hook and preserve other Codex hooks. Run `bash test-codex.sh` to check the adapter locally.

## Usage statusline for Claude Code + Codex (optional)

One shared core `bin/usage/core.py` and two thin shells render the same two-line footer in both agents:

```
<model> · ctx N% · lượt: X in / Y out · + $c · tổng $t
cache: read R · write W · new N · hit H% · K req | phiên: Q req, P% từ cache
```

- `bin/usage/claude.py`: Claude `statusLine` command (payload on stdin, cost from Claude, still forwards the payload to Orca's hook).
- `bin/usage/codex_mcp.py`: Codex MCP stdio `tui.status_line_provider`; tokens from `$CODEX_HOME/sessions` logs, prices from `bin/usage/rates.json`.
- `bin/usage/install.py install [--replace] [--only claude|codex]` · `uninstall` · `status`. Also `install.sh --with-statusline` (not part of `--full`). Files go to `~/.agent-usage/`.
- An existing statusLine / status_line_provider is kept unless `--replace`; the previous value is saved in `~/.agent-usage/previous.json` and restored by `uninstall`. Codex edits are a marked block plus one tagged `[tui]` line, validated with `tomllib` before writing.

## Active rules

| ID | Name | Type | Blocks? | What it does |
|---|---|---|---|---|
| R4 | audit-log | `PostToolUse` hook | no | Appends every Write/Edit/Bash (Bash secret-redacted) to `.claude/audit/audit.jsonl` and a readable `log.md`; every block appends to `decisions.jsonl` |
| R8 | session-health | `SessionStart` hook | no | Reports rule count and checks policy drift |
| R19 | knowledgelib-nudge | `UserPromptSubmit` hook | no | **Optional.** Every N prompts, reminds the agent to query `knowledgelib_search`; silent unless KnowledgeLib is installed (`HARNESS_KNOWLEDGELIB=on/off` forces it) |
| R20 | self-docs-canonical | `require_frontmatter` | yes (session + repo) | **Optional.** `self-docs/*.md` must have 6 canonical frontmatter fields and a non-empty body; only fires in repos that have `self-docs/` |
| R21 | self-docs-sync | `Stop` hook | no | **Optional.** Sanitizes and syncs self-docs into KnowledgeLib at the end of a session; does nothing without the store |
| R22 | orca-browser-only | `PreToolUse` hook | yes | Forbids opening the system browser; use the Orca built-in browser |

## Changing rules

Edit `policy.yaml`, then run `python3 gen-converters.py` (writes `out/`) or re-run `install.sh` (generates and wires in one step). Do not edit adapter code to add a rule.

Each rule has `enforce_at`: `session` (hook/CLI blocks at write time) or `repo` (pre-commit and CI).

### Preview the consequences before installing (plan → replay)

Ideas borrowed from [open-ontologies](https://github.com/fabio-rovai/open-ontologies): preview the consequences of a change, measure them on real data, and keep evidence that someone else can re-check. Implemented here as plain scripts, with no reasoner.

```bash
python3 gen-converters.py --plan                        # = bin/harness-plan.py: working tree vs HEAD
python3 bin/harness-plan.py --base v1 --diff            # another baseline, with a unified diff of out/
python3 bin/harness-plan.py --discover ~/Documents      # + blast radius on installed projects (with replay)
python3 bin/harness-plan.py --fail-on high              # exit 1 on any high-risk change (for CI)
python3 bin/harness-replay.py --project /path/to/proj   # run the candidate engine + policy on real audit logs
python3 bin/harness-replay.py --engine /tmp/cand/bin --project P --fail-on-new-blocks
```

- **plan** never writes the real `out/`. It generates the wiring for both the baseline and the working tree in a temp dir, then diffs them. It scores each change: `high` = a new or stricter block at session, or a changed engine behind a blocking rule; `medium` = CI may go red, a changed matcher, or a removed block; `low` = text-only changes or loosening. For each installed project it reports which commit the installed policy matches, which rules a reinstall adds or removes, and how many past calls would now be blocked.
- **replay** reads `audit.jsonl` (calls that were allowed) and `decisions.jsonl` (calls that were blocked), re-evaluates them with the **same pure functions** the hooks use (`llmwiki-validate.evaluate`, `harness-events.REPLAYABLE`), and reports: still allowed · still blocked · **NEWLY BLOCKED** · newly allowed · not measurable. Limits, printed on every run: Write/Edit are measured on the file's *current* content; Bash commands are the redacted copies; audit logs before 2026-11-04 have no Bash commands. When you add a blocking hook, register its check in `REPLAYABLE` in `harness-events.py`, or replay will list the rule as not replayable.
- **decisions.jsonl**: every Claude hook block records the rule, the matched fragment, `input_sha`, `policy_sha` and `engine_sha`, which is enough to re-check why a call was blocked. Disable with `HARNESS_NO_DECISIONS=1`; stop recording Bash commands in the audit with `HARNESS_AUDIT_NO_BASH=1`. Redaction is pattern-based (prefixed tokens, `Authorization`, `user:pass@`, `*_TOKEN=`/`*_KEY=` variables, `--password`, `mysql -p`, private key blocks), so it is **not a guarantee**.

## Browser policy (R22)

**R22 orca-browser-only** is a `PreToolUse` (Bash) hook. It blocks (exit 2) commands that open the system default browser (`open <url|*.html>`, `open -a <browser>`, `xdg-open`, `python -m webbrowser`, `osascript ... open location`) and points to the Orca browser (`orca tab create --url ...`).

- If a site refuses the embedded browser (e.g. Google sign-in), print the URL for the user to paste; do not fall back to Chrome.
- Temporary unlock: `HARNESS_ALLOW_SYSTEM_BROWSER=1`.
- Only the leading token of each shell segment is inspected, so commit messages containing `open http...` are not blocked.
- Known gap: `sudo -u ... open` is not caught (fail-open).

## Language code rules (rules-pull)

Code rules per language (Go, JS/TS, ...) live in KnowledgeLib as KUs at `software/coding-rules/<lang>-code-rules.md`. The harness pulls them into each repo:

```bash
python3 bin/rules-pull.py --lang js-ts,go --root /path/to/repo [--kl ~/Documents/Repo/knowledgelib_data]
python3 bin/rules-pull.py --lang go --diff          # show what changed vs rules.lock, no write
python3 bin/rules-pull.py --lang go --check         # exit 1 if the repo drifted from the KU (for CI)
python3 bin/rules-pull.py --lang go --wire-claude   # add @docs/rules/go.md to CLAUDE.md
```

- Generates `docs/rules/<js|go>.md` (do not hand-edit) and `rules.lock` (version + per-rule hash, so every update shows a diff).
- `rules.local.yaml` (written by the repo, never overwritten): `overrides: [{id, action: disable|severity, severity, reason}]`. **`reason` is required.**
- `rules.local.md` (written by the repo, never overwritten): repo-specific notes (stack, conventions), appended verbatim to the end of `docs/rules/<out>.md` under `## Ghi chú riêng của repo (rules.local.md)`.
- `rules.lock` tracks `local_notes_sha`: editing or deleting `rules.local.md` makes `--check` report drift and `--diff` print `~ rules.local.md`.
- **Verdict by rule source**: each rule set carries a keyword. `standard` = the KU standard set, unmodified. `with_local_overrides` = `rules.local.yaml` disabled rules or changed their severity, so a "pass" in this repo is not a pass against the standard. The keyword is printed on pull, stored in `rules.lock` (`verdict`) and shown at the top of `docs/rules/<out>.md`. Rules with a changed severity are marked on their own line.
- No lint config (eslint/golangci) is generated from the data yet, only documentation.
- Tests: `bash test-rules.sh`.

### Proposing new rules from a repo (rules-propose)

A review queue for rule proposals going back to the KU, with approval before merge:

```bash
# Add a proposal to rules-proposals/<lang>/<ID>.yaml
python3 bin/rules-propose.py add --lang go --id GO-ERR-05 --severity warn --kind review \
  --statement "..." --evidence "..." --origin "..." [--scope prod,tests] [--root .] [--kl PATH]

# List proposals (pending / merged)
python3 bin/rules-propose.py list [--lang go] [--root .]

# Merge a proposal into the KU (bumps version, updates last_verified; requires approval)
python3 bin/rules-propose.py merge --lang go --id GO-ERR-05 --approve-by "<name>" [--patch] [--root .] [--kl PATH]
```

- Tests: `bash test-propose.sh`.

## KnowledgeLib and self-docs (R19–R21)

KnowledgeLib is **one shared knowledge store for all your repos**, registered globally in `~/.claude.json` (`mcpServers.knowledgelib`), not as a project-scoped `.mcp.json`. Install with `--with-knowledgelib` (or `--full`):

```bash
KNOWLEDGELIB_HOME=/path/to/knowledgelib_data bash install.sh /path/to/project --with-knowledgelib
```

`KNOWLEDGELIB_HOME` defaults to `~/Documents/Repo/knowledgelib_data`. Idempotent: an existing entry is left alone.

`--with-knowledgelib` also installs the **`knowledgelib` skill** from `$KNOWLEDGELIB_HOME/SKILL.md` (real copy in `~/.agents/skills/knowledgelib`, symlinked from `~/.claude/skills/`). An existing skill is not overwritten; a version mismatch is only reported so you can update it yourself.

- **R19 knowledgelib-nudge**: `UserPromptSubmit` hook reminding the agent to consult KnowledgeLib for domain knowledge.
- **R20 self-docs-canonical**: gates writes to `self-docs/*.md`, requiring 6 YAML frontmatter fields (`id`, `canonical_question`, `aliases`, `entity_type`, `domain`, `last_verified`) and a non-empty body.
- **R21 self-docs-sync**: `Stop` hook that sanitizes (strips PII / company names) and pushes `self-docs/` to the central KnowledgeLib, and rebuilds its memory index. Can be run by hand: `python3 bin/sync-to-knowledgelib.py`.

**Architecture principle: on-demand RAG vs working memory**
- **Zero eager context ingestion**: never load the whole KnowledgeLib or its index into the agent context at session start. Context is for the current project's working memory (`CLAUDE.md`, task context), so a growing store does not pollute context or exhaust the token budget.
- **Pull on demand**: the agent calls the `knowledgelib_search` MCP tool only for domain questions that are indexed.
- Results are a **baseline and reference**, not ground truth; the agent is expected to cross-check and add current, deeper knowledge of its own.

**Moving to a home server later:** change one place, the `mcpServers.knowledgelib` entry in `~/.claude.json` (`command` / `args` / `env`). No project needs touching, since every repo points to that single global entry.

## Doctor

Run `python3 bin/harness-doctor.py [--project <path>] [--json]` with Python 3.11 or later. Doctor reads the checkout, skills, local configuration, and usage statusline files, and lists command paths from `PATH`. The project defaults to the current directory. It exits 1 if any check reports `FAIL` and 0 otherwise. Open `/hooks` in Codex to verify trust.

## Tests

```bash
bash demo.sh           # 8 quick cases (R20 path/hook/files, fail-open, wiring generation)
bash test-broad.sh     # 66 cases (R20 canonical, robustness, strict files mode + real CI step, R22 browser-guard, decisions.jsonl, redaction)
bash test-plan.sh      # 31 cases: harness-plan (risk scoring, installed projects) + harness-replay
bash test-rules.sh     # rules-pull (including the standard / with_local_overrides verdict)
bash test-propose.sh   # rules-propose
bash test-usage.sh     # 44 cases: usage statusline (core, Claude shell, Codex MCP shell, installer)
bash test-doctor.sh    # read-only diagnostics, JSON, and exit codes
```

## Not included (specific to the original project, not vendor-neutral)

- Rules removed on 2026-10-15 (R1–R3, R5–R7, R9–R18: raw/wiki/proposal/ADR/pull-gate/seq-glass/no-ai-attribution) and their production validators (`proposal_complete.py`, `decision_adr.py`, `no_ai_attribution.py`, `patterns_guard.py`, `report_show_path.py`). To recover them, see `git log -- policy.yaml` before the slimming commit.
- A `~/.claude/harness` global engine and `install-harness.sh --global`: a global-shared mechanism of the older bootstrap, not needed for this minimal set.

## Optional network fetches (opt-in, OFF by default)

Nothing downloads or runs remote code on its own. These activate only if you set the env var, pointing at a source you trust:
- `REPO_RAW=<raw url>`: `install.sh --with-wiki` downloads overstack.html / templates and may run `install-harness.sh --global` from that source.
- `HARNESS_REMOTE_POLICY=<raw url of policy.yaml>`: the session-start hook compares your policy with that copy.

## License

MIT. Use, modify and redistribute freely, including as part of your own product. See [LICENSE](LICENSE).

Exception: skills under `skills/` keep their original authors' licenses (MIT / Apache-2.0); see [skills/NOTICE.md](skills/NOTICE.md).
