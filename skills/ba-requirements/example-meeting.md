# Thử `/ba-requirements` trên bản ghi cuộc họp có đáp án (repo bên thứ ba)

Dữ liệu: `transcript.txt` (bản ghi họp hư cấu, 4 người) và `notes-groundtruth.txt` (ghi chú yêu cầu do chính tác giả viết làm đáp án) trong
`saiganeshm093/requirements-extraction-assistant`, commit `69fc4db`, repo 0 sao, **không có giấy phép**.
Vì vậy repo này **không chép** hai tệp; chỉ ghi tóm tắt và thang chấm tự viết. Muốn chạy lại thì tải hai tệp đó về thư mục riêng.

Red-team repo (2026-11-28): 7 tệp, quét sạch (không ký tự ẩn, không câu tiêm lệnh, không lệnh nguy hiểm). `extract.js` gọi một API LLM bằng khoá trong `.env`; **không chạy**.

## Tóm tắt đầu vào

Bốn người họp về sai lệch giữa tổng chi tiêu trong ứng dụng và tổng giao dịch. Sản phẩm muốn có gì đó hiện ra cho khách sớm; kỹ thuật chưa biết nguyên nhân;
tuân thủ yêu cầu tìm nguyên nhân trước và duyệt mọi lời nhắn gửi khách; một người chen vào sự cố lỗi đăng nhập Android (không cùng chủ đề); có các việc được giao cuối họp; một quyết định (ẩn, giữ, hay cảnh báo cạnh tổng chi tiêu) còn để ngỏ.

## Thang chấm (tự viết, đối chiếu với đáp án của tác giả repo)

| # | Phải thấy trong đầu ra |
|---|---|
| 1 | **Việc được giao tách khỏi yêu cầu**: ai điều tra nguyên nhân, ai gom ví dụ khiếu nại, ai soạn lời nhắn, ai duyệt. Ghi người và hạn, không thành `FR`. |
| 2 | Banner tạm thời là `FR`; banner **không được nói sự cố đã khắc phục**. |
| 3 | **Mâu thuẫn trong nguồn**: bản nháp của kỹ thuật bảo khách "xem danh sách giao dịch để biết số mới nhất", còn tuân thủ cấm hàm ý danh sách đó chính xác khi chưa được xác nhận. Nêu cả hai kèm mã nguồn; thành câu hỏi mở. |
| 4 | **Duyệt của tuân thủ trước khi phát hành** nằm ở ràng buộc/quy tắc quy trình, không phải một `FR` của ứng dụng. |
| 5 | **Lỗi Android nằm ngoài phạm vi**, kèm lý do và gợi ý ghi nhận riêng. |
| 6 | **Quyết định chưa chốt** (ẩn, giữ hay thêm cảnh báo) nằm trong câu hỏi mở, không bị chọn thay. |
| 7 | Mốc "hai đến ba ngày" ghi là **phụ thuộc** (kết quả điều tra, duyệt), không phải cam kết. |
| 8 | Độ mơ hồ ≥ 30% (mục tiêu "khách tin lại số liệu" chưa đo được): dừng và hỏi, không xuất bản "sạch". |
| 9 | Câu hỏi suy ra mà nguồn không nhắc: banner hiện ở màn hình nào ("dùng ở nhiều chỗ"), khi nào gỡ, tiêu chí thành công. |

## Kết quả chạy tay lần đầu (2026-11-28)

Đạt 6/9 mục (2, 3, 5, 6, 7, 8). Trượt:
- Mục 1: skill chưa có loại "việc cần làm"; các việc được giao bị lẫn vào yêu cầu hoặc rơi mất.
- Mục 4: skill chưa nói quy tắc quy trình (duyệt, hạn chót) khác yêu cầu hệ thống.
- Mục 9: chỉ được một phần (câu hỏi "khi nào gỡ banner" ra nhờ bước kiểm "mỗi quy trình có trạng thái kết thúc", còn "hiện ở màn hình nào" thì không).

Đã vá bằng cách thêm loại "việc cần làm" và "quyết định chưa chốt" vào bước 2, quy tắc "quy trình không phải FR", và gợi ý hỏi nơi hiển thị. Chạy lại tay (cũng do chính tôi, không phải phiên độc lập) đạt 9/9; cần một phiên mới chạy bài này để xác nhận.

## Kết quả phiên độc lập (2026-11-28, `claude -p`, chỉ có quyền Read/Write/Glob/Grep)

Chạy trong thư mục chỉ có `transcript.txt`, bằng một phiên Claude Code mới, không liên quan phiên viết skill.

- **Lần 1:** đạt 8/9, mục 4 đạt một phần: viết "Compliance duyệt trước khi phát hành" thành `FR-2` dù skill đã dặn là quy tắc quy trình. Độ mơ hồ 63%, dừng và hỏi đúng.
- **Đã vá** quy tắc: không viết thành FR **kể cả khi công cụ cưỡng chế được**; nếu có vẻ cần thì thêm câu hỏi mở.
- **Lần 2 (sau vá, phiên mới):** quy tắc duyệt nằm ở ràng buộc và có câu hỏi mở Q8 "có cần hệ thống cưỡng chế không"; tên người thay bằng vai trò; đủ 9/9 với một lưu ý: `FR-1` vẫn chép câu "khách nên xem danh sách giao dịch" mà tuân thủ đang cấm ngụ ý, dù mâu thuẫn đó đã được nêu ở ràng buộc, `AC-1.2` và câu hỏi Q7. Độ mơ hồ 80%, dừng và hỏi.

Một phiên mỗi lần, chưa lặp nhiều lần để đo độ ổn định.
