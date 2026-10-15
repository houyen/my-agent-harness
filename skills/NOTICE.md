# Third-party notice

The skills in this directory are vendored, with path adjustments, from
<https://github.com/rheinmir/setup> at commit `5c5cca9b0ebdd560a99809f740d48eaf127792ca`
(branch `orca`), where they were authored by Rheinmir and published under the MIT License:

- `impact-check`, `safe-change`, `md-to-html`, `playwright-verify`, `skill-provenance`, `web-crawl`
- `web-crawl/scripts/web-crawl.py`, `web-crawl/scripts/bnal_config.py`
- `skill-provenance/scripts/skill-provenance.py`

Changes from upstream: script paths in `SKILL.md` point to the installed location
(`~/.claude/skills/<name>/scripts/...`) instead of the upstream repo layout.

Skills that upstream itself pulled from other authors (the `caveman*` family, `agent-reach`, ...)
are NOT vendored here; their own licenses apply. Install them from their original source.

---

MIT License

Copyright (c) 2026 Rheinmir

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
