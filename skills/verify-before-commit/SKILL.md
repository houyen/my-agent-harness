---
name: verify-before-commit
description: Cổng trước mỗi git commit — chạy gate của repo (verify/typecheck/lint/test), soát staging (không secret, không git add -A), commit message nói vì sao. Dùng ngay trước khi tạo git commit, hoặc khi user nói "commit", "verify trước commit", "/verify-before-commit".
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "2.0.0-personal"
  origin: "rheinmir/setup verify-before-commit 1.0.0, tái chế 2026-11-27 bỏ llmwiki promote/task lifecycle"
---

# Skill: verify-before-commit

## WHAT
- **Purpose:** không commit thứ chưa kiểm, không lọt secret, không stage nhầm file của người/phiên khác.
- **Non-goals:** không viết tính năng; không tự push trừ khi user yêu cầu; không bỏ bước vì "thay đổi nhỏ".

## HOW
1. **Tìm gate của repo** theo thứ tự, dùng cái đầu tiên có:
   1. Lệnh gate khai trong `CLAUDE.md`/`AGENTS.md` (ví dụ `pnpm verify`).
   2. Script `verify`/`check`/`test`/`typecheck`/`lint` trong `package.json` (theo package manager của lockfile).
   3. `Makefile` target `check`/`test`; `go build ./... && go vet ./... && go test ./...`; `pytest`; `cargo test`.
   Không tìm được gate nào → nói rõ "repo không có gate", chạy cái kiểm được (typecheck/lint), không im lặng bỏ qua.
2. **Chạy gate.** Đỏ → sửa rồi chạy lại; không commit khi đỏ. Không dùng `--no-verify`.
3. **Smoke** khi thay đổi chạm luồng chính: chạy thật golden path (CLI chạy lệnh mẫu, server gọi endpoint, UI kiểm bằng `playwright-verify`). Test xanh không thay được smoke cho thay đổi hành vi.
4. **Soát staging:**
   - `git branch --show-current` — đúng nhánh chưa; đang ở nhánh mặc định mà repo yêu cầu nhánh riêng → tạo nhánh.
   - `git status` — file lạ (sửa/untracked không do mình) là của phiên khác: để nguyên.
   - Stage từng file cụ thể: `git add <file>`. Cấm `git add .`, `git add -A`, `git commit -a`.
   - Cấm stage `.env*`, `*.pem`, `*.key`, `*token*`, `*credential*`, `service-account*.json`, API key.
   - `git diff --cached --stat` trước khi commit.
5. **Commit message** nói *vì sao*, không kể lại diff. Theo quy ước repo (ngôn ngữ, Conventional Commits, trailer bắt buộc). Có `caveman-commit` thì dùng để viết.
6. **Báo kết quả:** hash commit + gate đã chạy + kết quả. Bước nào bỏ qua thì nói bỏ qua và vì sao.

## Failure boundaries
- Gate đỏ → blocked, chưa commit.
- Phát hiện secret trong diff → dừng, báo user, không commit.
- Hook pre-commit chặn → sửa nguyên nhân, không bypass.
