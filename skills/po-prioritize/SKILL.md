---
name: po-prioritize
description: "Xếp ưu tiên backlog bằng RICE hoặc WSJF có script tính điểm, cắt theo sức chứa, rồi gán MoSCoW cùng user. Số liệu do user hoặc dữ liệu thật cung cấp, không bịa. Gõ tay: /po-prioritize"
disable-model-invocation: true
metadata:
  origin: "Tự viết (2026-11-28). RICE, WSJF và MoSCoW là phương pháp công khai; không sao chép skill của bên thứ ba. scripts/score.py là mã gốc, chỉ dùng thư viện chuẩn."
---

# po-prioritize

Giúp Product Owner xếp thứ tự việc cần làm bằng số, rồi đối chiếu số với phán đoán. Điểm chỉ hỗ trợ quyết định, không thay nó.

## Quy trình

1. **Lấy danh sách ứng viên** từ `requirements.md` (các `FR-n`), ticket của `/to-tickets` hoặc backlog user đưa. Mỗi mục có mã và tên ngắn.
2. **Chọn một phương pháp, không trộn:**
   - **RICE** khi đo được số người bị ảnh hưởng (sản phẩm hướng người dùng): `reach × impact × confidence ÷ effort`.
   - **WSJF** khi giá trị là hỗn hợp (giá trị kinh doanh, độ gấp, giảm rủi ro), hợp việc nội bộ và hạ tầng: `(giá trị + độ gấp + giảm rủi ro) ÷ kích thước`.
3. **Thu số liệu từ user hoặc dữ liệu thật. Không tự điền.** Mỗi con số ghi nguồn (số đo, hay ước lượng của ai). Thiếu số thì hỏi; chưa có thì mục đó chờ, không đưa vào bảng.
   - RICE: `reach` là số người hoặc sự kiện mỗi kỳ; `impact` theo thang 3 (rất lớn), 2, 1, 0.5, 0.25; `confidence` 1, 0.8 hoặc 0.5; `effort` tính bằng người-tuần.
   - WSJF: ba chỉ số giá trị và `job_size` theo thang tương đối 1, 2, 3, 5, 8, 13, 20.
4. **Ghi `.scratch/<slug>/priority-input.json`** và chạy:
   `python3 -I ~/.claude/skills/po-prioritize/scripts/score.py .scratch/<slug>/priority-input.json --format md --capacity <N>`
   `--capacity` là tổng công sức team làm được trong kỳ; bỏ nó đi nếu chưa có.
5. **Phản biện kết quả** trước khi trình:
   - Điểm chênh nhau dưới 10% coi như hoà; quyết bằng phụ thuộc, rủi ro hay chiến lược.
   - Mục có `confidence` thấp nằm gần đầu bảng thì đề xuất làm thử hoặc nghiên cứu trước khi cam kết.
   - Mục hạng thấp nhưng là phụ thuộc kỹ thuật của mục hạng cao thì kéo lên và nói rõ vì sao.
6. **Gán MoSCoW cùng user.** Must là mục vào sức chứa **và** bắt buộc (pháp lý, cam kết). Should là mục vào sức chứa. Could là mục ngay dưới vạch. Won't là phần còn lại, kèm lý do.
7. **Xuất `.scratch/<slug>/priorities.md`:** bảng xếp hạng, vạch sức chứa, nguồn và độ tin cậy của số liệu, các chỗ phản biện ở bước 5, bảng MoSCoW, các quyết định còn chờ user.

Xong khi mỗi mục trong bảng có số liệu có nguồn, user đã xác nhận MoSCoW, và mọi mục bị loại có lý do.

## Quy tắc

- **Không bịa số.** Số ước lượng ghi rõ là ước lượng và của ai.
- **Không so điểm giữa RICE và WSJF** và không so điểm giữa hai kỳ dùng thang khác nhau.
- **Không chỉnh số để ra thứ hạng mong muốn.** Muốn đổi thứ hạng vì lý do ngoài điểm thì ghi lý do đó ở bước 5.
- Script chỉ đọc file JSON và in kết quả, không mạng, không ghi file.

## Định dạng đầu vào

```json
{
  "method": "rice",
  "items": [
    {"id": "FR-1", "name": "Khách tự hoàn tiền", "reach": 800, "impact": 2, "confidence": 0.8, "effort": 4}
  ]
}
```

WSJF dùng `business_value`, `time_criticality`, `risk_reduction`, `job_size` thay cho bốn trường trên.

## Bước kế

Có `priorities.md` đã chốt → `/to-tickets` cho các mục Must và Should. Việc quá lớn hoặc còn mù mờ → `/wayfinder`. Mục cần xác nhận với người khác → `/to-questionnaire`.
