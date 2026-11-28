---
name: ba-requirements
description: "Biến biên bản họp, email, ghi chú hoặc spec thô thành tài liệu yêu cầu có mã: yêu cầu chức năng theo mẫu EARS (FR-n), tiêu chí chấp nhận GIVEN/WHEN/THEN, yêu cầu phi chức năng đo được, điểm mơ hồ, danh sách câu hỏi mở và ma trận truy vết về nguồn. Gõ tay: /ba-requirements"
disable-model-invocation: true
metadata:
  origin: "Viết lại bằng lời riêng, rút ý từ Rune-kit/rune skills/ba (MIT, 2026-11-28) và kỹ thuật EARS (Mavin và cộng sự). Không sao chép văn bản hay mã. Phần nhúng hệ sinh thái Rune (cook, scout, plan, .out-of-scope, tín hiệu emit) đã bỏ."
---

# ba-requirements

Làm rõ **cái gì** cần xây, không phải **xây thế nào**. Không viết code, không lập kế hoạch thi hành.
Đầu vào: văn bản thô (biên bản họp, email, ghi chú, spec chưa gọn). Đầu ra: `.scratch/<feature-slug>/requirements.md`.

## Quy trình

1. **Ghi nguồn.** Gán mã cho từng nguồn: `S1`, `S2`... kèm ai nói, ngày, loại (họp, email, spec). Giữ nguyên câu gốc để trích dẫn.
2. **Phân loại phát biểu.** Mỗi ý trong nguồn là một trong: mục tiêu, quy tắc nghiệp vụ, ràng buộc, yêu cầu chức năng, yêu cầu phi chức năng, giả định, quyết định đã chốt, câu hỏi mở. Mỗi ý giữ mã nguồn của nó.
3. **Tự trả lời trước khi hỏi.** Câu nào đọc được từ nguồn, README, tài liệu hay code thì **không hỏi user**. Câu nào không có trong tài liệu mới đưa vào danh sách hỏi.
4. **Chấm độ mơ hồ** theo ba chiều, mỗi chiều 0.0 đến 1.0:

   | Chiều | 0.0 | 0.5 | 1.0 |
   |---|---|---|---|
   | Mục tiêu | "làm tốt hơn" | "tăng tốc trang tổng quan" | "trang tải dưới 2 giây với 10.000 dòng" |
   | Ràng buộc | chưa nhắc | "dùng DB hiện có" | "PostgreSQL 15, không thêm thư viện, tuân thủ GDPR" |
   | Tiêu chí thành công | "chạy được" | "người dùng thấy dữ liệu" | "có AC kiểm được bằng GIVEN/WHEN/THEN" |

   Độ mơ hồ = 1 trừ trung bình ba chiều. **Từ 30% trở lên thì dừng và hỏi**, bằng `/grill-me` (hỏi user) hoặc `/to-questionnaire` (hỏi người khác). Từ 15% đến dưới 30%: đi tiếp, mọi chỗ hở ghi thành câu hỏi mở. Dưới 15%: đi tiếp. Con số chỉ để định hướng, không phải đo chính xác.
5. **Viết yêu cầu chức năng theo EARS.** Mỗi yêu cầu có mã `FR-n`, đúng một "phải" (shall), chủ thể là một thành phần cụ thể, không dùng "nó". Chọn mẫu đơn giản nhất còn đủ:

   | Mẫu | Dạng |
   |---|---|
   | Luôn đúng | Hệ thống `<X>` phải `<phản hồi>`. |
   | Theo sự kiện | Khi `<sự kiện>`, `<X>` phải `<phản hồi>`. |
   | Theo trạng thái | Khi đang ở `<trạng thái>`, `<X>` phải `<phản hồi>`. |
   | Tuỳ chọn | Nếu có `<tính năng>`, `<X>` phải `<phản hồi>`. |
   | Điều kiện lỗi | Nếu xảy ra `<tình huống không mong muốn>`, thì `<X>` phải `<phản hồi>`. |
   | Kết hợp | Khi đang ở `<trạng thái>` và xảy ra `<sự kiện>`, `<X>` phải `<phản hồi>`. |

   Phản hồi phải kiểm được ("trả mã 401"), không dùng "xử lý êm", "nhanh". Không nhét cách cài đặt vào yêu cầu (không nêu Redis, tên bảng). Yêu cầu nào toàn là mẫu "luôn đúng" thường là đã bỏ sót sự kiện kích hoạt.
6. **Tiêu chí chấp nhận.** Mỗi `FR-n` có ít nhất một `AC-n.m` dạng GIVEN/WHEN/THEN, nêu dữ liệu cụ thể.
7. **Yêu cầu phi chức năng** (`NFR-n`): hiệu năng, bảo mật, khả dụng, tuân thủ. Mỗi cái có con số và cách đo.
8. **Phạm vi:** tách "trong phạm vi" và "ngoài phạm vi", mỗi mục ngoài phạm vi kèm lý do.
9. **Kiểm nhất quán trước khi bàn giao**, mỗi dòng đánh 🟢 / 🟡 / 🔴:
   - mỗi AC dẫn về một FR
   - mỗi FR dẫn về một nguồn (hoặc ghi "suy luận, cần xác nhận")
   - phạm vi trong và ngoài không giẫm lên nhau
   - mỗi quy trình có trạng thái kết thúc
   - mỗi NFR có con số
   - mỗi câu hỏi mở có chủ và hạn
   Còn 🔴 thì **không bàn giao**; nói rõ chỗ nào và hỏi.
10. **Xuất file** theo mẫu dưới. Xong khi bước 9 không còn 🔴 và mỗi FR có AC.

## Quy tắc

- **Không bịa yêu cầu.** Ý nào không có trong nguồn thì ghi "suy luận, cần xác nhận" hoặc đưa vào câu hỏi mở.
- **Nguồn mâu thuẫn nhau thì liệt kê cả hai**, kèm mã nguồn; không tự chọn bên nào.
- **Không viết HOW.** Chuyển cách làm sang `/plan` hoặc `tdd`.
- Dữ liệu nhạy cảm trong biên bản (tên, số điện thoại, tài khoản): thay bằng vai trò hoặc mã trước khi ghi ra file.

Ví dụ chạy trọn một biên bản (hư cấu) từ đầu đến bàn giao: [example.md](example.md).

## Mẫu `requirements.md`

```markdown
# <Tên tính năng>: yêu cầu
Nguồn: S1 (họp 2026-11-20, A và B), S2 (email khách 2026-11-22)
Độ mơ hồ: 18% (mục tiêu 0.9, ràng buộc 0.7, tiêu chí 0.8)

## Phạm vi
Trong: ... | Ngoài: ... (lý do)

## Yêu cầu chức năng
- FR-1 [S1] Khi khách gửi đơn thiếu địa chỉ, form phải hiển thị lỗi ở trường địa chỉ.
  - AC-1.1 GIVEN đơn không có địa chỉ WHEN khách bấm Gửi THEN trường địa chỉ có thông báo lỗi và đơn không được lưu.

## Yêu cầu phi chức năng
- NFR-1 [S2] Trang xác nhận đơn tải dưới 2 giây ở phân vị 95 với 10.000 đơn (đo bằng ...).

## Giả định · Rủi ro
## Câu hỏi mở
| # | Câu hỏi | Chủ | Hạn |

## Truy vết
| Nguồn | FR | AC | NFR |

## Kiểm nhất quán
(🟢/🟡/🔴 từng dòng)
```

## Bước kế

Có `requirements.md` sạch → `/ba-test-design` (từ FR và tham số sinh bộ test), `/po-prioritize` (xếp thứ tự các FR), `/to-spec` (đưa lên tracker hoặc file spec), rồi `/to-tickets`. Còn mơ hồ → `/grill-me` hoặc `/to-questionnaire`.
