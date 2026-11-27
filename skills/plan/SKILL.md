---
name: plan
description: >-
  Mở rộng một SPEC ĐÃ DUYỆT thành kế hoạch thi hành mà một agent KHÔNG có context (subagent, opencode/Gemini,
  CLI headless không hỏi lại được) vẫn làm đúng: đường dẫn file chính xác, Interfaces giữa các task, ràng buộc
  chép nguyên văn, bước có lệnh chạy + output mong đợi, và brief giao việc. Gọi khi user nói "viết plan",
  "plan thi hành", "chuẩn bị brief cho agent", "/plan". Không dùng khi chưa có SPEC duyệt (dùng /propose).
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "2.0.0-personal"
  origin: "rheinmir/setup plan 1.0.0, tái chế 2026-11-27 bỏ llmwiki/orca dispatch/validator"
---

# Skill: plan

Cái gì không nằm trong PLAN thì agent thi hành không có. Agent rẻ gặp chỗ mơ hồ sẽ đoán rồi im lặng.

## WHAT
- **Trigger:** SPEC đã duyệt; việc nhiều bước/nhiều file; hoặc sắp giao cho agent khác (subagent, opencode, Gemini).
- **Non-goals:** không thiết kế lại (đó là `/propose`); không dùng cho sửa một dòng.
- **Nơi ghi:** theo quy ước repo (`CLAUDE.md`/`AGENTS.md`). Mặc định: thêm mục `## Kế hoạch thi hành` vào cuối file SPEC, hoặc `docs/PLAN-<tên>.md` nếu SPEC nằm trên chat.

## HOW
1. **Đọc SPEC đã duyệt** — lấy nguyên `Ràng buộc chung`, `FR-xxx`, `SC-xxx`, `Các bước`.
2. **Scope check** — SPEC ôm nhiều hệ con độc lập → tách nhiều plan, mỗi plan tự chạy được và test được.
3. **`### File structure` trước khi chia task** — mọi file tạo/sửa + trách nhiệm từng file. Đọc code thật để khai đường dẫn và chữ ký thật.
4. **Chia task kiểu tracer bullet** — mỗi task là lát cắt dọc chạy được và chứng minh được một mình. Ngoại lệ: thay đổi cơ học lan khắp codebase → expand (thêm dạng mới) → migrate theo lô → contract (xoá dạng cũ).
5. **Viết từng task theo khuôn:**
   ```markdown
   ### Task N: <tên>
   **Thoả:** FR-001, FR-003
   **Files:** Tạo `a/b.ts` · Sửa `c/d.ts:120-145` · Test `tests/d.test.ts`
   **Interfaces:** Consumes <chữ ký từ task trước> · Produces <tên hàm, kiểu vào/ra cho task sau>
   **Depends:** Task 1 (hoặc —)
   **Verify:** `<lệnh rc 0 = xong thật>`
   - [ ] Step 1: viết test fail (code test thật)
   - [ ] Step 2: chạy `<lệnh>` → mong đợi FAIL `<thông báo>`
   - [ ] Step 3: code tối thiểu (code thật)
   - [ ] Step 4: chạy lại → PASS
   ```
   Bước đổi code phải có code; lệnh phải chính xác kèm output mong đợi. Theo pattern sẵn có, không refactor tiện tay.
6. **Self-review, sửa tại chỗ:** (a) mỗi `FR-xxx` có task nhận; (b) không placeholder: `TBD`, "xử lý lỗi phù hợp", "viết test cho phần trên" không kèm code, "tương tự Task N"; (c) tên hàm/kiểu khớp giữa các task.
7. **Brief giao việc** (khi giao agent khác) — mỗi task một brief, chép NGUYÊN VĂN task + `Ràng buộc chung`, không tóm tắt. Khung: **làm gì · xong khi (một lệnh đo) · cấm · ngân sách · báo cáo**. Repo có quy ước giao việc riêng (ví dụ `AGENTS.md`, worktree) → theo quy ước đó.

## Cổng ngược — /plan được quyền bác SPEC
DỪNG, không viết plan nửa vời, khi: một yêu cầu không quy về task nào được; hai mục SPEC mâu thuẫn hoặc trái `Ràng buộc chung`; phương án đã chọn bất khả thi (file/API không tồn tại); phải bịa hàm/kiểu/file SPEC không nhắc. Gom TẤT CẢ chỗ vỡ thành một lần báo, mỗi chỗ kèm câu SPEC gây ra, rồi quay về `/propose`.

## Examples
- SPEC export CSV có FR-001..003 → 3 task tracer bullet, mỗi task có Files/Interfaces/Verify `pnpm test tests/export.test.ts` → brief giao opencode chép nguyên văn từng task.
- Khai File structure thì lộ ra API mà SPEC chọn không tồn tại → dừng, báo một lần, quay lại `/propose`.
