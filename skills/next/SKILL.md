---
name: next
description: "Hỏi 'giờ nên dùng skill nào?': đọc tình hình (hội thoại, git, file .scratch/) rồi chỉ ra một skill kế tiếp và lý do. Chỉ gợi ý, không chạy. Gõ tay: /next"
disable-model-invocation: true
---

# next

Chỉ ra skill kế tiếp cho tình huống hiện tại. Không chạy skill đó.

## Cách làm

1. **Đọc tình hình, đừng hỏi trước.** Dùng đoạn hội thoại gần nhất, rồi xem nhanh:
   `git status -s`, `git log -3 --oneline`, và có hay không `.scratch/*/spec.md`, `.scratch/*/issues/`, `GLOSSARY.md`.
2. **Xác định giai đoạn** bằng bảng dưới. Dấu hiệu từ repo thắng cảm đoán:
   - có `spec.md` mà chưa có `issues/` → `/to-tickets`
   - có thay đổi chưa commit và code đã xong → `/qc-code`, sau đó `/verify-before-commit`
3. **Trả lời đúng ba dòng:** skill chính (gõ gì), vì sao hợp lúc này, và nhiều nhất hai phương án khác kèm điều kiện chọn chúng.
4. **Không rõ giai đoạn** thì hỏi đúng MỘT câu, rồi trả lời theo bước 3. Xong khi bạn đã nêu được một skill chính.

## Bảng giai đoạn

| Tình huống | Skill |
|---|---|
| Yêu cầu mơ hồ, chưa rõ cần gì | `/grill-me` |
| Cần chốt thuật ngữ hay quyết định kiến trúc | `/grill-with-docs` |
| Câu trả lời nằm ở người khác (khách, stakeholder) | `/to-questionnaire` |
| Việc quá lớn cho một phiên, còn mù mờ | `/wayfinder` |
| Đã bàn đủ, cần chốt thành tài liệu | `/to-spec` (tổng hợp) hoặc `/propose` (viết spec rồi dừng chờ duyệt) |
| Có spec, cần chia việc | `/to-tickets` |
| Giao cho agent không có ngữ cảnh | `/plan` |
| Đang làm một ticket | `tdd` |
| Sắp sửa code dùng chung | `impact-check`, rồi `safe-change` |
| Có lỗi hoặc sự cố | `/orca-issue` |
| Có biên bản họp hay ghi chú thô, cần thành yêu cầu có mã | `/ba-requirements` |
| Cần bộ test case từ yêu cầu (nhiều tham số) | `/ba-test-design` |
| Code xong | `/qc-code`, rồi `/verify-before-commit` |
| Không hiểu tin nhắn vừa rồi | `/wait-what` |
| Muốn hiểu sâu một thứ | `/teach-me` |
| Cần nghiên cứu sâu, có trích nguồn | `research` |
| Cần đọc Reddit, X, YouTube | `/agent-reach` (gửi truy vấn ra ngoài) |
| Sắp hết phiên | `/orca-handover` |

Bảng này là ảnh chụp ngày 2026-11-27. Skill mới thêm vào harness thì cập nhật bảng cùng lúc.
