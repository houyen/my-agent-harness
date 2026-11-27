---
name: propose
description: Viết SPEC cho một tính năng/thay đổi TRƯỚC khi code rồi DỪNG chờ duyệt — restate, ảnh hưởng, phương án có tradeoff, FR/SC đánh id, giả định khai rõ. Gọi khi user nói "propose", "viết spec", "đề xuất trước khi làm", "/propose". Không viết code, không viết kế hoạch thi hành (đó là /plan).
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "2.0.0-personal"
  origin: "rheinmir/setup propose 1.0.0, tái chế 2026-11-27 bỏ llmwiki/archify/validator"
---

# Skill: propose

## WHAT

- **Purpose:** chốt thiết kế với người duyệt trước khi tốn công code. SPEC là thứ NGƯỜI đọc để gật/bác; kế hoạch code-level là việc của `/plan` sau khi SPEC được duyệt.
- **Trigger:** tính năng/endpoint/component mới; thay đổi đụng code dùng chung; phạm vi mơ hồ, hiểu được nhiều cách.
- **Non-goals:** không viết code; không viết bước TDD/đường dẫn dòng (đó là `/plan`); không phỏng vấn user trừ khi được yêu cầu.

### Nơi ghi SPEC
1. Repo có quy ước trong `CLAUDE.md`/`AGENTS.md` (ví dụ `docs/PLAN-<tên>.md`) → theo đúng quy ước đó.
2. Không có → `docs/PLAN-<tên-kebab>.md`.
3. Việc nhỏ hoặc user muốn trên chat → trình bày SPEC ngay trong chat, không tạo file.

## HOW

1. **Đọc bối cảnh trước khi viết** — `CLAUDE.md`, `AGENTS.md`, `docs/STATUS.md` hoặc tương đương, plan/ADR liên quan, memory dự án. Tóm vào `## Bối cảnh`, dẫn đường dẫn.
2. **Liệt kê unknown** — "để làm đúng việc này tôi CHƯA biết gì?". Soi 5 chỗ: ý định ngầm của người yêu cầu; quy ước không ghi ở đâu; hình dạng dữ liệu thật; môi trường chạy (version, env, quyền); thứ đã đổi kể từ khi tài liệu được viết.
3. **Phân fact / decision:**
   - Fact (tra được bằng một lệnh, đọc file, grep) → TRA, không hỏi.
   - Decision rủi ro thấp → tự điền, gắn `(default)`.
   - Decision có rủi ro, biết sẽ phải kiểm lại → `(default, kiểm lại sau)` và ghi vào `## Nợ mở`.
   - Decision mà sai là hỏng kiến trúc hoặc hỏng người dùng → `[CẦN LÀM RÕ: <câu hỏi cụ thể>]`. Nhóm này gồm: xác thực/phân quyền; lưu dữ liệu gì, ở đâu, bao lâu, ai đọc; tiền/hạn mức; pháp lý/tuân thủ; ranh giới tin cậy (input ngoài).
4. **Viết SPEC** với các mục:
   - `## Yêu cầu` — restate một câu.
   - `## Bối cảnh` — từ bước 1.
   - `## Ràng buộc chung` — chép NGUYÊN VĂN giá trị thật (version, gate bắt buộc, quy ước đặt tên, luật repo). Mọi task sau mang theo mục này.
   - `## Ảnh hưởng` — mọi file/hàm/module phải đổi (dùng `impact-check` khi đụng symbol dùng chung). Rỗng → ghi "Không ảnh hưởng code hiện có."
   - `## Rủi ro phụ` — tính năng/hành vi có thể gãy theo.
   - `## Không làm` — non-goals; thiếu mục này thì phạm vi trôi.
   - `## Phương án` — 2–3 phương án khác nhau về bản chất, tradeoff từng cái, chọn cái nào và vì sao. Cấm chọn thầm.
   - `## Yêu cầu chức năng` — `**FR-001**: Hệ thống PHẢI …` (id ổn định để `/plan` truy vết).
   - `## Tiêu chí thành công` — `**SC-001**: …` đo được, nói người dùng nhận được gì; lệnh máy (test/verify) ghi làm bằng chứng của SC, không thay SC.
   - `## Giả định` — mọi chỗ tự điền, gắn `(default)` hoặc `[CẦN LÀM RÕ]`.
   - `## Nợ mở` — các `(default, kiểm lại sau)`: giá trị đã điền, cần kiểm gì, khi nào.
   - `## Các bước` — checklist `- [ ]` mức task, chưa tới code.
5. **Self-review, sửa tại chỗ:** (a) mỗi yêu cầu của user về đúng một task; (b) không còn `TBD`/`TODO`/"xử lý phù hợp"/"tương tự task N"; (c) cùng một thứ gọi cùng một tên xuyên suốt.
6. **DỪNG.** Hiện SPEC (hoặc đường dẫn file), chờ duyệt. Còn `[CẦN LÀM RÕ]` → hỏi từng câu một, kèm phương án khuyến nghị đặt đầu.
7. **Sau khi duyệt** → đề nghị `/plan` nếu việc nhiều bước hoặc sẽ giao agent khác; việc nhỏ thì code trực tiếp.

## Failure boundaries
- Còn `[CẦN LÀM RÕ]` chưa trả lời → không coi là đã duyệt.
- User chưa duyệt → không code.
- User bảo "cứ đoán" cho một `[CẦN LÀM RÕ]` → hạ xuống `(default)` có chủ ý, ghi vào `## Nợ mở`.

## Examples
- "thêm nút xuất PDF lá số" → SPEC `docs/PLAN-export-pdf.md`: ảnh hưởng `web/src/...`, 2 phương án (render server vs client) có tradeoff, FR-001..003, SC đo người dùng, màu nút `(default)` → dừng chờ duyệt.
- "cho người khác xem lá số của tôi" → `[CẦN LÀM RÕ: ai được xem, link có hết hạn không?]` → hỏi trước khi coi SPEC là xong.
