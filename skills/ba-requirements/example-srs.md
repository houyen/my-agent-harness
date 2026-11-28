# Thử `/ba-requirements` trên một SRS thật có sẵn lỗi (bộ PURE)

Dữ liệu thật, công khai, dùng để kiểm hồi quy: một tài liệu yêu cầu do người khác viết, có lỗi tự nhiên mà người soạn không cố ý cài.
Repo này **không chép** tài liệu; chỉ trích tối đa một câu ngắn kèm số mục.

## Lấy dữ liệu

- Bộ PURE (Ferrari, Spagnolo, Gnesi, IEEE RE 2017), bản ghi Zenodo [1414117](https://zenodo.org/records/1414117), giấy phép ghi trên bản ghi: CC BY 4.0. Quyền của từng tài liệu bên trong thì người duy trì bộ dữ liệu nói họ không biết có thoả thuận nào; vì vậy chỉ dùng để thử, không đưa lại vào repo.
- Tệp `requirements-xml.zip` (378.737 byte, MD5 `c81235c40f88a2c947ae66e0eddad585`). Tải vào thư mục riêng, kiểm MD5, giải nén bằng công cụ kiểm tên tệp, **không chạy gì từ trong đó**.
- Tài liệu dùng: `2003 - qheadache.xml`, SRS của một trò chơi xếp khối ("Qheadache", khoảng 13.000 ký tự khi bỏ thẻ XML).
- Quét red-team cả 18 tệp XML của gói: không có câu tiêm lệnh, lệnh nguy hiểm hay đoạn base64. Chỉ có ghi chú trình soạn thảo trong chú thích XML, ký tự BOM đầu tệp (9 tệp) và một ký tự vùng riêng U+F8E7 trong `2008 - peering.xml` (dấu vết chuyển từ PDF); không tệp nào là tệp đang dùng ở đây.

## Chạy tay lần đầu (2026-11-28)

Độ mơ hồ: mục tiêu 0.8, ràng buộc 0.6, tiêu chí thành công 0.5 → trung bình 0.63 → **độ mơ hồ 37%, tức dừng và hỏi** theo ngưỡng 30% của skill.

## Thang chấm: lỗi trong nguồn mà skill phải phát hiện

Skill đạt khi nêu được **ít nhất 9 trong 12 mục** dưới đây, và không bịa giá trị cho mục nào.

| # | Lỗi hoặc chỗ thiếu | Vị trí |
|---|---|---|
| 1 | Độ sâu undo: "một nghìn thao tác" (§2.2.1) lệch với "10000 vị trí trước" khi lưu (§3.2.4.2); "Lưu thành" không nêu giới hạn (§3.2.4.3) | §2.2.1, §3.2.4.2, §3.2.4.3 |
| 2 | Điều kiện kích thước x: "không nhỏ hơn 50 và lớn hơn 100" không thể xảy ra; nghi là 50 ≤ x ≤ 100, biên chưa rõ | §3.2.1.1 |
| 3 | Điều kiện thắng "khối vuông lớn chuyển xuống đáy" không nói chạm mép hay đúng vị trí đích | §3.2.2.1.2 |
| 4 | Ba tên trạng thái cho cùng một việc (di chuyển khối, chọn khối, dịch chuyển), không có sơ đồ trạng thái | §3.2.1.2 đến §3.2.1.4 |
| 5 | Hộp thống kê chỉ hiện khi số nước đi **thấp hơn mức cao nhất đã ghi**; khi bảng chưa đủ 10 mục thì người chơi bị bỏ khỏi bảng dù còn chỗ | §3.2.2.1.4 và §3.2.3.2.3 |
| 6 | Xếp hạng chỉ theo số nước đi; thời gian bị bỏ qua dù §2.2.4 nói điểm gồm cả hai; chưa nói cách xử lý hoà | §2.2.4, §3.2.3.2.3 |
| 7 | "Undo được tính như một nước đi": có tăng bộ đếm không? | §3.2.1.5.3 |
| 8 | "Chạy trên mọi HĐH Qt hỗ trợ" mâu thuẫn "di động sang Windows" | §2.1.3, §3.4 |
| 9 | Mục "Yêu cầu hiệu năng" chỉ nói "một người dùng mỗi máy"; không có con số hiệu năng nào | §3.3 |
| 10 | Thoát khi "chưa lưu": chưa nói trường hợp đã lưu nhưng sửa sau đó | §3.2.4.4.3 |
| 11 | Tên người chơi tối đa 20 ký tự; chưa nói tên rỗng hay ký tự cấm | §3.2.2.2.1 |
| 12 | Tệp thống kê: vị trí và định dạng chưa nêu; lỗi ghi chỉ có "thông báo lỗi" chung chung | §3.2.3.2.4 |

## Kết quả bàn giao sang `/ba-test-design`

Thử với phần undo/redo: tham số `Hành động liền trước` (chưa có nước đi, di chuyển khối, undo, redo), `Mục menu thử` (Undo, Redo), `Độ sâu lịch sử` (0, 1, 1000, 1001, 10000): 20 dòng thay cho 40 tổ hợp. Các dòng độ sâu 1001 và 10000 có kết quả mong đợi **chưa rõ** vì mục 1 ở trên chưa được chốt. Đó là hành vi mong muốn của skill.

## Kết quả phiên độc lập (2026-11-28, `claude -p`, chỉ có quyền Read/Write/Glob/Grep)

Phiên mới đọc bản văn bản của SRS (`srs.txt`, rút từ XML). Độ mơ hồ 47%, dừng và hỏi; vẫn ghi bản nháp đánh dấu "CHƯA BÀN GIAO".

Phát hiện khoảng 11/12 lỗi trong thang chấm (các mục 1 đến 11; mục 12 về vị trí và định dạng tệp thống kê không thấy nêu rõ), vượt ngưỡng 9. Nó còn nêu thêm lỗi khác (lề 0.1x so với 0.05x, thiếu "ván mới", hiển thị giờ không có yêu cầu), tôi chưa kiểm từng lỗi thêm này với nguồn.

Hạn chế: bản nháp dài (khoảng 29 KB, 37 FR, 24 câu hỏi mở); nó thay tên và email tác giả trong cửa sổ About bằng chỗ giữ chỗ, hơi thừa với một tài liệu công khai.
