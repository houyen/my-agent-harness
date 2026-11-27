---
name: research
description: "Điều tra MỘT câu hỏi lớn từ nguồn gốc (tài liệu chính thức, mã nguồn, spec) bằng agent nền, ghi kết quả có trích dẫn vào một file Markdown trong repo. Dùng khi user nói 'nghiên cứu sâu', 'research có trích nguồn', 'gom tài liệu về X vào file'. KHÔNG dùng để tra nhanh một câu (dùng tìm web thường) và không dùng cho mạng xã hội (agent-reach)."
---

Spin up a **background agent** to do the research, so you keep working while it reads. Start it with a fresh context window.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

## Bước kế

Có kết quả mà kế hoạch còn mơ hồ → `grilling`. Đã đủ để quyết → `/propose`.
