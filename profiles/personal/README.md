# Profile `personal`

Hồ sơ Claude Code toàn cục (`~/.claude`) cho máy cá nhân. Nguồn chân lý cho skill, chế độ hiển thị skill,
tuỳ chọn settings và hướng dẫn toàn cục. Phần riêng tư (memory dự án, skill chưa rõ giấy phép) nằm ở một
repo riêng, truyền vào bằng `--private DIR` hoặc biến `MAH_PRIVATE_DIR`.

| File | Vai trò |
|---|---|
| `CLAUDE.md`, `RTK.md` | Hướng dẫn toàn cục. Đã có bản khác thì chỉ báo lệch; `--force-docs` để thay (có sao lưu). |
| `settings.json` | Các khoá profile quản trong `~/.claude/settings.json` (model, effort, theme, `skillOverrides`...). Khoá khác giữ nguyên. |
| `skills.json` | Skill riêng (repo riêng), skill ngoài (Orca, knowledgelib) và công cụ CLI cần có. Skill công khai = mọi thư mục `skills/`. |
| `skill-hints.json` | Cụm từ → skill gợi ý cho hook `bin/skill-hint.py` (UserPromptSubmit). Hook chỉ in tối đa 2 gợi ý, không chạy skill, tắt bằng `SKILL_HINT_OFF=1`. Log tên skill ở `~/.claude/skill-hint.log`. |
| `Brewfile` | Công cụ cài qua Homebrew. |

## Máy mới

1. Cài Homebrew, rồi `brew bundle --file profiles/personal/Brewfile`.
2. Cài tay:
   - Claude Code: `curl -fsSL https://claude.ai/install.sh | bash`.
   - Orca (ứng dụng). Orca tự cài `orca-cli`, `orca-computer-use` và hook của nó.
   - Codex (tuỳ chọn).
3. `bash install.sh --profile personal --private <repo-riêng>/claude-profile --with-moli`
   - Skill được symlink về checkout, nên về sau `git pull` là cập nhật xong.
   - Hook llmwiki cũ bị gỡ. Mọi thay đổi đều sao lưu vào `~/.claude/profile-backups/<giờ>/`.
   - `--with-moli` tải và chạy script cài chính thức của Moli (lexmount/moli). Bỏ cờ này thì `web-crawl` tự lùi về backend `builtin`.
4. Chạy thêm:
   - `bash install.sh --with-knowledgelib`
   - `rtk init -g`
   - `python3 bin/usage/install.py install` (statusline)
5. Khôi phục memory: `bash <repo-riêng>/claude-profile/restore-memory.sh`.
6. Đăng nhập bằng tay: `claude`, `gh auth login`, opencode.
7. Kiểm: `python3 bin/harness-doctor.py --profile personal --private <repo-riêng>/claude-profile`.

## Lệnh

```bash
python3 bin/profile.py install [--private DIR] [--dry-run] [--force-docs] [--with-moli] [--keep-legacy-hooks]
python3 bin/profile.py check   [--private DIR] [--json]     # rc 1 khi có lỗi
python3 bin/profile.py context [--private DIR]              # ước lượng token profile nạp đầu phiên
```
