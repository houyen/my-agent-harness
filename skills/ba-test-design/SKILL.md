---
name: ba-test-design
description: "Thiết kế bộ test case tổ hợp tối thiểu (pairwise/t-way) từ yêu cầu hoặc spec: tách tham số, giá trị, ràng buộc, sinh bảng test, gắn kết quả mong đợi và truy vết về yêu cầu. Gõ tay: /ba-test-design"
disable-model-invocation: true
metadata:
  origin: "Quy trình tham khảo ý tưởng từ omkamal/pypict-claude-skill (MIT, 2026-11-28). Viết lại bằng lời riêng; không sao chép mã, không dùng gói pypict. Bộ sinh test là scripts/pairwise.py tự viết, chỉ dùng thư viện chuẩn."
---

# ba-test-design

Biến yêu cầu thành bộ test ít nhất mà vẫn phủ mọi cặp giá trị (hoặc ba giá trị với `--strength 3`).
Dùng khi một tính năng có nhiều tham số độc lập và test đầy đủ là quá nhiều dòng.

## Quy trình

1. **Lấy tham số từ yêu cầu.** Đọc spec, ticket hoặc đoạn code. Nếu đã có `requirements.md` từ `/ba-requirements`, lấy tham số từ các `FR-n` và dùng chính mã đó làm cột truy vết. Mỗi đầu vào, cấu hình hay điều kiện môi trường ảnh hưởng kết quả là một tham số.
   Nếu yêu cầu chưa nói rõ một giá trị hay ngưỡng, **không đoán**: ghi vào danh sách "chưa rõ" và hỏi user (dùng `grilling`, hoặc `/to-questionnaire` nếu người trả lời là người khác).
2. **Chọn giá trị** cho từng tham số bằng phân hoạch tương đương và giá trị biên. Mỗi lớp tương đương một giá trị đại diện; thêm giá trị biên cho tham số số học.
3. **Khai ràng buộc.** Mỗi quy tắc nghiệp vụ cấm một tổ hợp là một mục `forbidden`. Ghi lý do ngay cạnh.
4. **Ghi model** vào `.scratch/<feature-slug>/pairwise-model.json` (định dạng ở cuối file này).
5. **Sinh bảng test:**
   `python3 -I ~/.claude/skills/ba-test-design/scripts/pairwise.py .scratch/<feature-slug>/pairwise-model.json --format md`
   Thêm `--strength 3` cho phần rủi ro cao. Kết quả gồm số test, số cặp cần phủ và số cặp không đạt được do ràng buộc.
6. **Gắn kết quả mong đợi cho từng dòng**, lấy từ yêu cầu. Dòng nào yêu cầu không nói rõ thì ghi "Chưa rõ" và hỏi lại.
7. **Thêm ca âm và ca biên ngoài model:** đầu vào sai định dạng, rỗng, quá dài, quyền truy cập sai. Tổ hợp tham số không bao phủ các ca này.
8. **Xuất `.scratch/<feature-slug>/test-cases.md`** với cột: mã test, các giá trị tham số, kết quả mong đợi, mã yêu cầu liên quan (FR-id nếu có).

Xong khi mỗi dòng có kết quả mong đợi hoặc nằm trong danh sách "chưa rõ", và mỗi yêu cầu có ít nhất một dòng test.

## Quy tắc

- **Không bịa giá trị, ngưỡng hay kết quả mong đợi.** Thiếu thì hỏi.
- **Nói rõ giới hạn:** bộ pairwise chỉ bảo đảm phủ mọi cặp. Lỗi chỉ xuất hiện khi ba tham số trở lên cùng một giá trị có thể lọt. Với rủi ro cao dùng `--strength 3`.
- **Không dán model hay dữ liệu thật vào công cụ web trực tuyến.** Chạy script cục bộ.
- Script chỉ đọc file model và in kết quả. Không mạng, không ghi file.

## Định dạng model

```json
{
  "parameters": {
    "Thông tin đăng nhập": ["hợp lệ", "sai"],
    "2FA": ["bật", "tắt"],
    "Ghi nhớ thiết bị": ["có", "không"],
    "Số lần thất bại trước đó": [0, 1, 3]
  },
  "forbidden": [
    {"Thông tin đăng nhập": "sai", "Ghi nhớ thiết bị": "có"}
  ]
}
```

`forbidden` liệt kê các tổ hợp một phần không được xuất hiện cùng nhau. Mỗi giá trị phải có trong `parameters`.

## Bước kế

Có bảng test → viết test bằng `tdd`. Phát hiện yêu cầu mâu thuẫn hay thiếu → `/grill-me`. Cần gửi câu hỏi cho khách → `/to-questionnaire`.
