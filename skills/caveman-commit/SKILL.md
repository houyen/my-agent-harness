---
name: caveman-commit
description: >
  Write a Conventional Commits message compressed to intent only. Use for
  "write a commit", "commit message", /commit or /caveman-commit.
---

Write commit messages terse and exact. Conventional Commits format. No fluff. Why over what.

> Modified for my-agent-harness (2026-11-27): repo trailers kept and placed last, message language follows repo history, 72-char hard cap with 50 as a target. Upstream: JuliusBrussee/caveman v4.0.1, Apache-2.0.

## Before writing

- Read `git log -10 --format=%B` and match the repo's language (e.g. Vietnamese subjects stay Vietnamese), scope names and capitalization.
- Read the repo's CLAUDE.md/AGENTS.md for required trailers (e.g. `Guard-Change: <path>: <reason>`) and for the attribution line the session was told to add (e.g. `Co-Authored-By: ...`).

## Rules

**Subject line:**
- `<type>(<scope>): <imperative summary>` — `<scope>` optional
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`
- Imperative mood: "add", "fix", "remove" — not "added", "adds", "adding"
- Aim for ≤50 chars, hard cap 72 (diacritic-heavy languages run longer; the cap is what matters)
- No trailing period
- Match project convention for capitalization after the colon

**Body (only if needed):**
- Skip entirely when subject is self-explanatory
- Add body only for: non-obvious *why*, breaking changes, migration notes, linked issues
- Wrap at 72 chars
- Bullets `-` not `*`
- Reference issues/PRs at end: `Closes #42`, `Refs #17`

**Trailers (last paragraph):**
- Keep every trailer the repo or session requires: `Guard-Change:`, `Co-Authored-By:`, `Assisted-by:`, `Signed-off-by:`
- Put them in the final paragraph, separated by one blank line, and put nothing else in that paragraph, so `git log --format='%(trailers)'` parses them
- `Closes #42` / `Refs #17` go in the body above the trailer paragraph

**What NEVER goes in:**
- "This commit does X", "I", "we", "now", "currently" — the diff says what
- "As requested by..." — use Co-authored-by trailer
- Prose AI attribution in subject or body ("Generated with ..."). Attribution the repo or session requires goes in as a trailer, never dropped
- Emoji (unless project convention requires)
- Restating the file name when scope already says it

## Examples

Diff: new endpoint for user profile with body explaining the why
- ❌ "feat: add a new endpoint to get user profile information from the database"
- ✅
  ```
  feat(api): add GET /users/:id/profile

  Mobile client needs profile data without the full user payload
  to reduce LTE bandwidth on cold-launch screens.

  Closes #128
  ```

Diff: breaking API change
- ✅
  ```
  feat(api)!: rename /v1/orders to /v1/checkout

  BREAKING CHANGE: clients on /v1/orders must migrate to /v1/checkout
  before 2026-06-01. Old route returns 410 after that date.
  ```

## Auto-Clarity

Always include body for: breaking changes, security fixes, data migrations, anything reverting a prior commit. Never compress these into subject-only — future debuggers need the context.

## Boundaries

Only generates the commit message, including its trailers. Does not run `git commit`, does not stage files, does not amend. Output the message as a code block ready to paste. "stop caveman-commit" or "normal mode": revert to verbose commit style.
