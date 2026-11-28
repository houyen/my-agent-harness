---
name: design-taste-frontend
description: Dựng giao diện landing page, portfolio hoặc redesign không giống mẫu AI chung chung. Đọc brief, chọn hướng thiết kế, rồi code với hệ thống chữ, màu, khoảng cách nhất quán. Gọi khi user nói "thiết kế đẹp", "landing page", "portfolio", "đừng làm kiểu template AI", "design taste", hoặc /design-taste-frontend. Giao diện đã có sẵn cần nâng cấp thì dùng `redesign-existing-projects`.
---

# design-taste-frontend — giao diện có chủ đích

## Quy trình

1. **Đọc brief**: sản phẩm làm gì, ai dùng, một hành động chính của trang là gì. Thiếu thì hỏi tối đa 3 câu.
2. **Chọn một hướng** và viết ra một câu (ví dụ: "biên tập, nhiều khoảng trắng, chữ serif lớn"). Mọi quyết định sau phải phục vụ câu đó.
3. **Khoá hệ thống trước khi code**: thang chữ, bảng màu, nhịp khoảng cách, bán kính bo, độ sâu. Lưu thành CSS variables.
4. **Dựng khung nội dung thật**: dùng chữ thật, không "Lorem ipsum", không "Feature One".
5. **Tự duyệt** bằng danh sách dưới đây, rồi sửa.

## Hệ thống tối thiểu

- **Chữ**: tối đa 2 họ. Thang tỷ lệ cố định (ví dụ 1.25): 14, 16, 20, 25, 31, 39, 49. Tiêu đề dùng `clamp()`. Dòng chữ 55 đến 75 ký tự, `line-height` 1.5 cho thân bài.
- **Màu**: 1 màu nền, 1 màu chữ, 1 màu nhấn, 2 đến 3 mức xám. Mọi thứ khác suy ra từ đó. Tương phản chữ ≥ 4.5:1.
- **Khoảng cách**: bội của 4 hoặc 8 px. Khoảng cách giữa các section lớn hơn khoảng cách trong section.
- **Bố cục**: một lưới rõ (12 cột hoặc 2 đến 3 cột), căn lề trái nhất quán. Phá lưới là có chủ ý và chỉ một chỗ.
- **Chuyển động**: ngắn (150 đến 400 ms), phục vụ nghĩa (vào, ra, phản hồi). Luôn tôn trọng `prefers-reduced-motion`.

## Dấu hiệu "template AI" cần tránh

- Gradient tím-xanh trên nền trắng, card nào cũng bo to + bóng mờ giống nhau.
- Hero căn giữa với ba cột "tính năng" icon tròn, rồi bảng giá ba gói, rồi CTA lặp lại.
- Emoji làm icon, số liệu bịa ("10K+ người dùng"), lời chứng thực giả.
- Mọi thứ cùng cỡ chữ, cùng độ đậm; không có điểm nhấn thị giác.
- Hiệu ứng hover/scroll ở mọi phần tử.

## Kiểm tra trước khi giao

- [ ] Nhìn mờ mắt (blur) vẫn thấy được thứ tự đọc.
- [ ] Mọi chữ có tương phản đủ ở cả hai theme nếu có dark mode.
- [ ] Bàn phím: tab đi hết nút và link, focus nhìn thấy.
- [ ] 360 px không cuộn ngang; ảnh có `width`/`height` hoặc `aspect-ratio`.
- [ ] Mỗi trang có đúng một hành động chính nổi bật.

## Bước kế

Cần nâng cấp trang đã có → `redesign-existing-projects`. Cần hiệu ứng → `scroll-effects`, `css-scroll-driven-native`. Verify bằng `/playwright-verify`.
