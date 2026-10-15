# my-agent-harness

[Tiếng Việt](README.md) · **English**

A personal, minimal, vendor-neutral agent harness. One `policy.yaml` is the single source of truth; `gen-converters.py` generates the wiring for Claude Code, opencode, Cursor, Codex, Kiro, CI and pre-commit.

Origin: distilled from a larger private harness. On 2026-10-15 it was cut down from 22 rules to the 6 that actually leave a trace in use (audit logs and hooks). Rules for llmwiki / ADR / proposals / pull-gates were removed because no repo had anything for them to guard.

> Docs and rule statements in `policy.yaml` are written in Vietnamese. The code, CLI flags and file layout are language-neutral.

## Install into a project

```bash
git clone --depth 1 https://github.com/houyen/my-agent-harness.git /tmp/my-agent-harness
bash /tmp/my-agent-harness/install.sh /path/to/target-project
```

Flags:
- `--vendor claude,opencode,cursor,codex,kiro`: force the vendor list (default: auto-detect)
- `--no-verify`: skip running demo.sh + test-broad.sh after install
- `--clean`: remove a previous install first
- `--with-wiki`: seed an `llmwiki/` skeleton (raw/, wiki/..., index.md, log.md). Directories only; no rule guards the wiki any more
- `--with-skills`: install a small skill set (global, via `npx skills`, needs `SKILLS_REF`). Default 8 skills: `orca-cli`, `skill-provenance`, `failure-flywheel`, `impact-check`, `safe-change`, `caveman`, `caveman-commit`, `caveman-review`. Override with `SKILLS_LIST=a,b,c`; `SKILLS_ALL=1` installs everything as before
- `--with-knowledgelib`: register the KnowledgeLib MCP server globally (see below)
- `--with-rtk`: install the global rtk hook if the machine does not have it (`rtk init -g --auto-patch`)
- `--full`: all of the above (wiki, skills, knowledgelib, rtk)

Install is idempotent. CI and pre-commit are always installed (the vendor-neutral floor); per-vendor adapters are installed only for vendors found in the project.

## rtk (optional)

`rtk` is not a skill: it is a CLI proxy plus a command-rewrite hook that saves tokens. Its hook is **machine-global** configuration (`~/.claude/settings.json`); there is no per-repo hook.

- New repos get the "prefix every command with `rtk`" convention through `CLAUDE.md.template`.
- `install.sh` always reports rtk status. With `--with-rtk` (or `--full`) it runs `rtk init -g --auto-patch` when the machine has no hook, and does nothing if it is already there.
- Avoid plain `rtk init` (no `-g`): it only injects ~5 KB of instructions into the project CLAUDE.md, duplicating the template and the global `RTK.md`.

## Active rules

| ID | Name | Type | Blocks? | What it does |
|---|---|---|---|---|
| R4 | audit-log | `PostToolUse` hook | no | Appends every Write/Edit to `.claude/audit/audit.jsonl` and a readable `log.md` |
| R8 | session-health | `SessionStart` hook | no | Reports rule count and checks policy drift |
| R19 | knowledgelib-nudge | `UserPromptSubmit` hook | no | Every N prompts, reminds the agent to query `knowledgelib_search` |
| R20 | self-docs-canonical | `require_frontmatter` | yes (session + repo) | `self-docs/*.md` must have 6 canonical frontmatter fields and a non-empty body |
| R21 | self-docs-sync | `Stop` hook | no | Sanitizes and syncs self-docs into KnowledgeLib at the end of a session |
| R22 | orca-browser-only | `PreToolUse` hook | yes | Forbids opening the system browser; use the Orca built-in browser |

## Changing rules

Edit `policy.yaml`, then run `python3 gen-converters.py` (writes `out/`) or re-run `install.sh` (generates and wires in one step). Do not edit adapter code to add a rule.

Each rule has `enforce_at`: `session` (hook/CLI blocks at write time) or `repo` (pre-commit and CI).

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

- **R19 knowledgelib-nudge**: `UserPromptSubmit` hook reminding the agent to consult KnowledgeLib for domain knowledge.
- **R20 self-docs-canonical**: gates writes to `self-docs/*.md`, requiring 6 YAML frontmatter fields (`id`, `canonical_question`, `aliases`, `entity_type`, `domain`, `last_verified`) and a non-empty body.
- **R21 self-docs-sync**: `Stop` hook that sanitizes (strips PII / company names) and pushes `self-docs/` to the central KnowledgeLib, and rebuilds its memory index. Can be run by hand: `python3 bin/sync-to-knowledgelib.py`.

**Architecture principle: on-demand RAG vs working memory**
- **Zero eager context ingestion**: never load the whole KnowledgeLib or its index into the agent context at session start. Context is for the current project's working memory (`CLAUDE.md`, task context), so a growing store does not pollute context or exhaust the token budget.
- **Pull on demand**: the agent calls the `knowledgelib_search` MCP tool only for domain questions that are indexed.
- Results are a **baseline and reference**, not ground truth; the agent is expected to cross-check and add current, deeper knowledge of its own.

**Moving to a home server later:** change one place, the `mcpServers.knowledgelib` entry in `~/.claude.json` (`command` / `args` / `env`). No project needs touching, since every repo points to that single global entry.

## Tests

```bash
bash demo.sh           # 8 quick cases (R20 path/hook/files, fail-open, wiring generation)
bash test-broad.sh     # 38 cases (R20 canonical, robustness, R22 browser-guard)
bash test-rules.sh     # rules-pull
bash test-propose.sh   # rules-propose
```

## Not included (specific to the original project, not vendor-neutral)

- Rules removed on 2026-10-15 (R1–R3, R5–R7, R9–R18: raw/wiki/proposal/ADR/pull-gate/seq-glass/no-ai-attribution) and their production validators (`proposal_complete.py`, `decision_adr.py`, `no_ai_attribution.py`, `patterns_guard.py`, `report_show_path.py`). To recover them, see `git log -- policy.yaml` before the slimming commit.
- A `~/.claude/harness` global engine and `install-harness.sh --global`: a global-shared mechanism of the older bootstrap, not needed for this minimal set.
- The llmwiki skill (`npx skills add <owner>/<repo>#<ref> --global`) is installed separately and is not part of the harness. `install.sh --with-skills` needs an explicit `SKILLS_REF`.

## Optional network fetches (opt-in, OFF by default)

Nothing downloads or runs remote code on its own. These activate only if you set the env var, pointing at a source you trust:
- `REPO_RAW=<raw url>`: `install.sh --with-wiki` downloads overstack.html / templates and may run `install-harness.sh --global` from that source.
- `SKILLS_REF=<owner>/<repo>#<ref>`: `install.sh --with-skills`.
- `HARNESS_REMOTE_POLICY=<raw url of policy.yaml>`: the session-start hook compares your policy with that copy.

## License

MIT. Use, modify and redistribute freely, including as part of your own product. See [LICENSE](LICENSE).
