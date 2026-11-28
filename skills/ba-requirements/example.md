# Ví dụ chạy `/ba-requirements` (dữ liệu hư cấu)

## Đầu vào

**S1: họp 2026-11-20, chị Lan (vận hành) và anh Minh (kế toán).**
"Khách hay đòi hoàn tiền sau khi nhận hàng. Giờ vận hành làm tay, hay sót. Muốn khách tự bấm hoàn tiền trong 7 ngày kể từ ngày giao.
Đơn đã giao quá 7 ngày thì không cho. Hoàn về đúng phương thức khách đã trả. Kế toán phải thấy mọi khoản hoàn trong báo cáo cuối ngày. Hàng khuyến mãi thì chưa biết có cho hoàn không."

**S2: email anh Minh 2026-11-22.**
"Khoản hoàn trên 5 triệu cần quản lý duyệt. Báo cáo cuối ngày chốt lúc 23:00."

## Bước 2: phân loại

| Mã | Phát biểu | Loại |
|---|---|---|
| S1-a | Khách tự bấm hoàn tiền | mục tiêu |
| S1-b | Trong 7 ngày kể từ ngày giao | quy tắc nghiệp vụ |
| S1-c | Quá 7 ngày không cho hoàn | quy tắc nghiệp vụ |
| S1-d | Hoàn về đúng phương thức đã trả | ràng buộc |
| S1-e | Mọi khoản hoàn vào báo cáo cuối ngày | yêu cầu chức năng |
| S1-f | Hàng khuyến mãi chưa rõ | câu hỏi mở |
| S2-a | Trên 5 triệu cần quản lý duyệt | quy tắc nghiệp vụ |
| S2-b | Báo cáo chốt 23:00 | ràng buộc |

## Bước 4: độ mơ hồ

Mục tiêu 0.9, ràng buộc 0.8, tiêu chí thành công 0.7 → trung bình 0.8 → **độ mơ hồ 20%**. Trong khoảng 15 đến 30%: đi tiếp, mọi chỗ hở ghi thành câu hỏi mở (xem Q1 và Q2).

## Đầu ra: `.scratch/hoan-tien/requirements.md`

```markdown
# Hoàn tiền đơn hàng: yêu cầu
Nguồn: S1 (họp 2026-11-20, vận hành và kế toán), S2 (email kế toán 2026-11-22)
Độ mơ hồ: 20% (mục tiêu 0.9, ràng buộc 0.8, tiêu chí 0.7)

## Phạm vi
Trong: khách yêu cầu hoàn tiền; kiểm hạn 7 ngày; hoàn về phương thức đã trả; duyệt khoản trên 5 triệu; báo cáo cuối ngày.
Ngoài: hoàn một phần đơn; đổi hàng (chưa ai nhắc tới; xác nhận ở Q3).

## Yêu cầu chức năng
- FR-1 [S1-a, S1-b] Khi khách bấm "Hoàn tiền" trên đơn đã giao không quá 7 ngày, hệ thống phải tạo yêu cầu hoàn tiền ở trạng thái "chờ xử lý".
  - AC-1.1 GIVEN đơn giao hôm qua WHEN khách bấm Hoàn tiền THEN có một yêu cầu trạng thái "chờ xử lý" gắn đúng đơn.
  - AC-1.2 GIVEN đơn giao đúng 7 ngày trước WHEN khách bấm Hoàn tiền THEN yêu cầu được tạo (ngày thứ 7 còn hợp lệ; xác nhận ở Q2).
- FR-2 [S1-c] Nếu đơn đã giao quá 7 ngày, thì hệ thống phải từ chối yêu cầu và hiển thị lý do hết hạn.
  - AC-2.1 GIVEN đơn giao 8 ngày trước WHEN khách bấm Hoàn tiền THEN không có yêu cầu nào được tạo và màn hình nêu "đã quá 7 ngày".
- FR-3 [S1-d] Khi một yêu cầu hoàn tiền được duyệt, hệ thống phải hoàn số tiền về đúng phương thức thanh toán của đơn.
  - AC-3.1 GIVEN đơn trả bằng thẻ WHEN yêu cầu được duyệt THEN lệnh hoàn tiền gửi tới đúng thẻ đó, không gửi tới phương thức khác.
- FR-4 [S2-a] Nếu số tiền hoàn lớn hơn 5.000.000 đồng, thì hệ thống phải chuyển yêu cầu sang trạng thái "chờ quản lý duyệt" thay vì duyệt tự động.
  - AC-4.1 GIVEN khoản hoàn 5.000.001 đồng WHEN yêu cầu được tạo THEN trạng thái là "chờ quản lý duyệt".
  - AC-4.2 GIVEN khoản hoàn đúng 5.000.000 đồng WHEN yêu cầu được tạo THEN không cần quản lý duyệt.
- FR-5 [S1-e] Khi một khoản hoàn hoàn tất, hệ thống phải ghi khoản đó vào báo cáo cuối ngày của ngày hoàn tất.
  - AC-5.1 GIVEN khoản hoàn hoàn tất lúc 10:00 WHEN báo cáo chốt THEN khoản đó có trong báo cáo cùng ngày.

## Yêu cầu phi chức năng
- NFR-1 [S2-b] Báo cáo cuối ngày phải chốt lúc 23:00 theo giờ Việt Nam (đo bằng giờ phát hành báo cáo trong nhật ký).

## Giả định · Rủi ro
- Giả định (suy luận, cần xác nhận): "7 ngày kể từ ngày giao" tính theo ngày lịch, không theo giờ.
- Rủi ro: khoản hoàn lúc 22:59 và 23:01 rơi vào hai báo cáo khác nhau (xem Q4).

## Câu hỏi mở
| # | Câu hỏi | Chủ | Hạn |
|---|---|---|---|
| Q1 | Hàng khuyến mãi có được hoàn không? (S1-f) | chị Lan | 2026-12-01 |
| Q2 | Ngày thứ 7 tính là còn hạn hay đã hết hạn? | chị Lan | 2026-12-01 |
| Q3 | Hoàn một phần hay đổi hàng nằm trong phạm vi không? | anh Minh | 2026-12-01 |
| Q4 | Khoản hoàn sau 23:00 vào báo cáo ngày nào? | anh Minh | 2026-12-01 |

## Truy vết
| Nguồn | FR | AC | NFR |
|---|---|---|---|
| S1-a, S1-b | FR-1 | AC-1.1, AC-1.2 | |
| S1-c | FR-2 | AC-2.1 | |
| S1-d | FR-3 | AC-3.1 | |
| S2-a | FR-4 | AC-4.1, AC-4.2 | |
| S1-e | FR-5 | AC-5.1 | |
| S2-b | | | NFR-1 |
| S1-f | | | (Q1) |

## Kiểm nhất quán
- 🟢 mỗi AC dẫn về một FR
- 🟢 mỗi FR dẫn về một nguồn
- 🟡 AC-1.2 và Q2 phụ thuộc cùng một câu hỏi chưa trả lời
- 🟢 phạm vi trong và ngoài không giẫm lên nhau
- 🟡 hàng khuyến mãi (Q1) chưa có FR
- 🟢 NFR-1 có con số và cách đo
- 🟢 mỗi câu hỏi mở có chủ và hạn
Kết luận: 0 🔴, 2 🟡. Được bàn giao cho `/ba-test-design` với điều kiện ghi Q1 và Q2 là chưa rõ.
```

## Bàn giao sang `/ba-test-design`

Model cho FR-1, FR-3, FR-4: tham số `Hạn` (còn hạn, đúng 7 ngày), `Phương thức` (thẻ, ví, chuyển khoản), `Mức tiền` (dưới 5 triệu, đúng 5 triệu, trên 5 triệu). Trường hợp quá hạn (FR-2, AC-2.1) là ca âm riêng, thêm ở bước 7, không đưa vào model. Dòng nào liên quan hàng khuyến mãi ghi kết quả mong đợi "Chưa rõ (Q1)".
