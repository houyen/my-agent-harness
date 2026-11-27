# PLAN: dựng lại bộ Claude Code cá nhân trên máy mới

**Trạng thái:** đã duyệt và thi hành 2026-11-27 (chưa commit theo yêu cầu chủ dự án). Kết quả ở mục cuối.
**Phạm vi:** hồ sơ cá nhân `~/.claude`. Hồ sơ công việc `~/.claude-work` nằm ngoài plan này.

## Yêu cầu

Đổi sang máy khác thì chạy một lệnh, cộng vài bước đăng nhập bằng tay, là có lại đúng bộ skill, hook, cấu hình và trí nhớ dự án như máy hiện tại. my-agent-harness là nguồn chân lý cho mọi phần công khai được.

## Bối cảnh

- Ngày 2026-11-27 đã dọn bộ skill toàn cục: gỡ 58 skill, sau đó tái chế nhóm skill gắn với hệ llmwiki cũ.
- Hiện có bốn nguồn skill song song:
  1. `skills/` của repo này (8 skill, cài offline, có `SHA256SUMS`).
  2. `npx skills` từ `rheinmir/setup` (`~/.agents/.skill-lock.json`, 39 mục). Không được chạy `update` hay `add --all`, vì bản upstream ghi file vào `llmwiki/`.
  3. 9 bản tái chế riêng cho hồ sơ cá nhân: thư mục thật trong `~/.claude/skills/<tên>`, không có ở đâu khác.
  4. Skill đi kèm ứng dụng Orca (`orca-cli`, `orca-computer-use`).
- Bản tái chế số 3 chỉ tồn tại trên máy này. Mất máy là mất chúng.
- Hồ sơ công việc dùng chung `~/.agents/skills` qua symlink. Hiện nó có 60 symlink chết sau đợt dọn. Đây là việc riêng, không thuộc plan này.
- Repo này **công khai**. Repo riêng tư sẵn có `agents-skills` là kho kiểm kê cũ (2026-04), có thể dùng lại.

## Ràng buộc chung

- Repo công khai không chứa: memory dự án, email, đường dẫn tên người dùng thật, tên máy chủ, token, nội dung `~/.claude.json`.
- Không lưu secret trong bất kỳ repo nào, kể cả repo riêng. Đăng nhập (Claude Code, `gh`, opencode, Cloudflare Access) làm bằng tay.
- Skill lấy từ bên thứ ba vẫn giữ giấy phép và ghi nguồn trong `skills/NOTICE.md`. `rheinmir/setup` dùng giấy phép MIT.
- Installer phải idempotent. Mỗi lần sửa `~/.claude/settings.json` đều sao lưu trước. Không đè cấu hình người dùng ngoài các khoá do harness quản.
- Giữ Browser Policy R22: không cài Playwright hay Chromium cho hồ sơ cá nhân.

## Inventory: thành phần cần mang theo

| Thành phần | Vị trí hiện tại | Nguồn chân lý đề xuất | Công khai? |
|---|---|---|---|
| Hướng dẫn toàn cục | `~/.claude/CLAUDE.md`, `~/.claude/RTK.md` | `profiles/personal/` ở repo này | có, sau khi soát |
| Hiển thị skill | `skillOverrides` trong `~/.claude/settings.json` | `profiles/personal/skill-overrides.json` | có |
| Hook toàn cục | `hooks` trong `settings.json` (16 event) | tách: hook harness → repo này; hook llmwiki cũ → bỏ | có |
| Statusline usage | `~/.agent-usage/` | `bin/usage/install.py` (đã có) | có |
| Skill cá nhân | 4 nguồn ở mục Bối cảnh | `skills/` ở repo này | có |
| MCP knowledgelib | `~/.claude.json` | `install.sh --with-knowledgelib` (đã có) | có |
| Công cụ CLI | rtk, moli, orca, opencode, gh, pnpm, node, uv, codex | `profiles/personal/Brewfile` + ghi chú cài tay | có |
| Memory dự án | `~/.claude/projects/<đường-dẫn-mã-hoá>/memory/` | repo riêng | **không** |
| Cấu hình riêng | `~/.ssh/config`, quyền `permissions` riêng | repo riêng (không có khoá) | **không** |

## Không làm

- Không đồng bộ hồ sơ công việc, cũng không đồng bộ skill nhóm E: jenkins-agent-l3-deploy, uat-nonit-testcase, tc-run, agent-reach, book-to-skill.
- Không mang `~/.claude/harness`, tức engine llmwiki toàn cục cũ. README đã ghi "Không mang theo".
- Không tự động hoá đăng nhập.
- Không đồng bộ lịch sử phiên (`projects/*.jsonl`), cache, telemetry.

## Phương án

1. **Repo công khai (repo này) cộng repo riêng nhỏ.** Chọn phương án này.
   - Repo này giữ skill, profile, installer và doctor.
   - Repo riêng chỉ giữ memory và cấu hình riêng tư.
   - Ưu điểm: tách rõ phần công khai và phần riêng; repo này vẫn hữu ích cho người khác.
   - Nhược điểm: phải quản hai repo.
2. **Gom tất cả vào một repo riêng.**
   - Đơn giản hơn.
   - Nhưng mất bản công khai, và trộn phần dùng lại được với dữ liệu cá nhân.
3. **Dùng trình quản dotfile (chezmoi/yadm) cho toàn bộ `~/.claude`.**
   - Mạnh khi cần template theo từng máy.
   - Nhưng thêm một công cụ nữa, và vẫn phải tách phần riêng.
   - Mang trọn `~/.claude` dễ kéo theo rác: cache, bản sao lưu, phiên.

## Yêu cầu chức năng

- **FR-001**: Repo này PHẢI chứa mọi skill cá nhân đang dùng, gồm cả 9 bản tái chế và các skill `rheinmir/setup` còn giữ, với `NOTICE.md` và `SHA256SUMS` cập nhật. Như vậy máy mới không cần `npx skills`.
- **FR-002**: Repo này PHẢI có `profiles/personal/` chứa `CLAUDE.md`, `RTK.md`, `skill-overrides.json` và `Brewfile`.
- **FR-003**: PHẢI có lệnh `bash install.sh --profile personal` để:
  - cài skill vào `~/.claude/skills`;
  - gộp `skillOverrides` và hook harness vào `~/.claude/settings.json`, có sao lưu trước;
  - chép `CLAUDE.md`/`RTK.md` khi chưa có (có rồi thì chỉ báo lệch);
  - cài statusline.
- **FR-004**: `bin/harness-doctor.py --profile personal` PHẢI báo:
  - skill thiếu, thừa hoặc lệch checksum;
  - symlink chết trong `~/.claude/skills`;
  - `skillOverrides` lệch với profile;
  - công cụ CLI thiếu.
- **FR-005**: Repo riêng PHẢI có script `restore-memory` chép memory theo đường dẫn repo trên máy mới. Mã hoá đường dẫn là thay `/` bằng `-`. Đường dẫn khác thì phải có bảng ánh xạ.
- **FR-006**: Hook trỏ vào `~/.claude/harness` (hệ llmwiki cũ) PHẢI được gỡ khỏi `settings.json` cá nhân, hoặc profile PHẢI ghi rõ vì sao giữ lại. Hiện các hook này chỉ chạy khi repo có `llmwiki/.harness-stamp`, mà không repo cá nhân nào có.

## Tiêu chí thành công

- **SC-001**: Trên máy mới đã cài Homebrew, từ lúc clone tới khi một phiên Claude Code có đúng danh sách skill và chế độ hiển thị như máy cũ: dưới 15 phút, không kể thời gian đăng nhập.
  - Bằng chứng: `harness-doctor --profile personal` rc 0.
- **SC-002**: Không dòng nào của repo công khai chứa email, tên người dùng thật hay nội dung memory.
  - Bằng chứng: grep trong cổng CI.
- **SC-003**: Sửa một skill trên máy cũ rồi push, thì máy mới chỉ cần `git pull && bash install.sh --profile personal` là nhận đúng bản mới.

## Giả định

- Máy mới dùng macOS, có Homebrew. `(default)`
- Username và cây thư mục `~/Documents/Repo/git-repos/` giữ nguyên, để memory chép thẳng không cần ánh xạ. `(default, kiểm lại sau)`
- Repo riêng là `agents-skills`, dùng lại kho kiểm kê cũ. `(default)` Có thể đổi sang repo mới.
- Các skill D giữ ở chế độ gọi tay (hiệu ứng WebGL/GSAP/Lenis, design-taste...) cũng được vendor vào repo này, để một nguồn duy nhất. `(default)`
- Moli: cài bằng script phát hành chính thức của lexmount/moli qua cờ opt-in `--with-moli`; không cờ thì `web-crawl` lùi về `builtin`. (đã chốt)

## Nợ mở

- `skill-provenance` vẫn nhắc `orca-sec-scans` (đã xoá) như một công cụ bổ trợ. Cần sửa câu chữ khi vendor.
- `timeline` vẫn nhắc `/diagram` (đã xoá). Cần sửa khi vendor.
- `dark-mode-maker` nhắc `docs-site-macos` 6 lần (đã gỡ). Cần kiểm còn chạy được không trước khi vendor; không được thì bỏ.
- `agent-reach` đang nằm trong `skills/` của repo này, trái quyết định nhóm E. Cần gỡ khỏi bundle.

## Các bước

- [x] **Task 1: vendor skill.**
  - Chép 9 bản tái chế từ `~/.claude/skills/` cùng các skill `rheinmir/setup` còn giữ vào `skills/`.
  - Gỡ `agent-reach` khỏi bundle.
  - Cập nhật `NOTICE.md` và `SHA256SUMS`.
  - Thoả FR-001.
  - Verify: `bash test-doctor.sh` rc 0; `shasum -a 256 -c skills/SHA256SUMS` rc 0.
- [x] **Task 2: tạo `profiles/personal/`.**
  - Đưa vào `CLAUDE.md` và `RTK.md` đã soát: thay đường dẫn tuyệt đối bằng `~`, bỏ chi tiết riêng.
  - Thêm `skill-overrides.json` lấy từ `settings.json` hiện tại.
  - Thêm `Brewfile` cho rtk, gh, pnpm, node, uv, opencode, codex, cộng ghi chú cài tay Orca, Moli và Claude Code.
  - Thoả FR-002.
  - Verify: grep không ra `/Users/`, email hay tên máy chủ trong `profiles/`.
- [x] **Task 3: thêm cờ `--profile personal` vào `install.sh`.**
  - Gộp JSON có sao lưu.
  - Skill cài dạng thư mục thật, hoặc symlink về checkout repo này. Chọn symlink để `git pull` là cập nhật ngay.
  - Thoả FR-003.
  - Verify: chạy hai lần liên tiếp vào một HOME tạm (`HOME=$(mktemp -d)`), lần hai không đổi gì.
- [x] **Task 4: thêm `--profile personal` vào doctor.**
  - Thoả FR-004.
  - Verify: trên HOME tạm có một symlink chết và một override lệch, doctor phải báo cả hai, rc khác 0.
- [x] **Task 5: dọn hook llmwiki cũ khỏi `settings.json` cá nhân.**
  - Sao lưu trước khi dọn.
  - Thoả FR-006.
  - Verify: mở một phiên ở repo cá nhân, `/hooks` không còn hook `~/.claude/harness`.
- [x] **Task 6: memory trong repo riêng.**
  - Viết `restore-memory`.
  - Chép memory hiện tại vào repo riêng.
  - Thoả FR-005.
  - Verify: khôi phục vào HOME tạm rồi so `diff -r` với bản gốc.
- [x] **Task 7: diễn tập máy mới.**
  - Tạo user macOS mới (hoặc HOME tạm), làm theo README từ đầu, bấm giờ.
  - Thoả SC-001.

## Self-review

- Mỗi FR có task nhận: FR-001→T1, FR-002→T2, FR-003→T3, FR-004→T4, FR-005→T6, FR-006→T5.
- Không còn placeholder, ngoài một `[CẦN LÀM RÕ]` về Moli phải trả lời trước Task 2.
- "Bản tái chế" và "profile personal" dùng nhất quán xuyên suốt.

## Kết quả thi hành (2026-11-27)

- Task 1: `skills/` có 19 skill. Thêm 10 bản tái chế (gồm `orca-handover`, bổ sung sau khi tổng hợp phát hiện còn ghi vào `llmwiki/`), cộng `fable5` và `scroll-effects`. Đã gỡ `agent-reach`. `NOTICE.md` và `SHA256SUMS` đã cập nhật; `shasum -c` đạt.
- 13 skill chưa rõ giấy phép (code lấy từ CodePen, taste-skill, trích từ sản phẩm) được đặt ở repo riêng `claude-profile/skills`, không vendor vào repo công khai.
- Task 2: tạo `profiles/personal/` gồm `CLAUDE.md`, `RTK.md`, `settings.json`, `skills.json`, `Brewfile`, `README.md`.
- Task 3–4: thêm `bin/profile.py` (install/check/context), cờ `install.sh --profile`, `harness-doctor.py --profile`. `test-profile.sh` 18/18, `test-doctor.sh` 57/57, `test-broad.sh` 68/68.
- Task 5: đã áp profile lên máy hiện tại. Hook llmwiki cũ đã gỡ (bản sao lưu ở `~/.claude/profile-backups/`). `profile.py check` báo "profile khớp".
- Task 6: repo riêng có `save-memory.sh` và `restore-memory.sh` (có `path-map.txt` khi đổi đường dẫn), mặc định loại dự án công ty. Khôi phục vào HOME tạm rồi `diff -r` sạch.
- Task 7: diễn tập trên HOME trống, không tính brew và đăng nhập. Script chạy dưới 1 giây, ra 31 skill và 5 thư mục memory. Doctor chỉ cảnh báo 3 skill do ứng dụng Orca và knowledgelib cài.
- Phần nạp đầu phiên do profile thêm vào (`profile.py context`): khoảng 3,9k token. Gồm CLAUDE.md khoảng 1,6k và mô tả của 15 skill model thấy khoảng 2,3k.
