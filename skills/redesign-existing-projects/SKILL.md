---
name: redesign-existing-projects
description: Nâng cấp giao diện website hoặc app đã có lên chất lượng cao hơn mà không làm hỏng chức năng. Kiểm toán thiết kế hiện tại, nhận ra mẫu AI chung chung, sửa theo từng lớp. Gọi khi user nói "redesign", "làm đẹp lại trang này", "nâng cấp giao diện", "audit UI", hoặc /redesign-existing-projects. Dựng từ đầu thì dùng `design-taste-frontend`.
---

# redesign-existing-projects — nâng cấp có kiểm soát

Nguyên tắc: **không đổi hành vi**. Mỗi bước chỉ chạm lớp trình bày, có ảnh trước/sau.

## Quy trình

1. **Chụp hiện trạng** ở 360, 768, 1280 px (`/playwright-verify`). Lưu làm đường cơ sở.
2. **Kiểm toán** theo bảng dưới; ghi mỗi lỗi một dòng: vị trí, vấn đề, mức (cao/vừa/thấp).
3. **Khoá token**: gom màu, cỡ chữ, khoảng cách đang rải rác thành CSS variables trước khi sửa giao diện.
4. **Sửa theo lớp**, mỗi lớp một commit nhỏ: chữ → khoảng cách → màu → bố cục → chuyển động.
5. **So ảnh trước/sau** và chạy lại test của dự án. Hành vi đổi là lỗi, quay lại bước 4.

## Bảng kiểm toán

| Lớp | Dấu hiệu kém | Cách sửa |
|---|---|---|
| Chữ | nhiều cỡ lẻ, thân bài rộng hơn 75 ký tự, `line-height` sát | thang tỷ lệ, `max-width: 65ch`, `line-height` 1.5 |
| Khoảng cách | giá trị tuỳ tiện (13px, 22px) | bội của 4 hoặc 8; section lớn hơn nội bộ |
| Màu | quá nhiều màu nhấn, tương phản thấp, đen/trắng tuyệt đối | 1 màu nhấn, xám có sắc, tương phản ≥ 4.5:1 |
| Bố cục | mọi khối cùng trọng lượng, căn giữa tràn lan | tạo một điểm nhấn, căn trái cho chữ dài |
| Thành phần | card bo to bóng giống nhau, icon emoji | một phong cách bo, một độ sâu, icon cùng bộ |
| Trạng thái | thiếu hover, focus, disabled, loading, rỗng, lỗi | bổ sung đủ trạng thái |
| Chuyển động | hiệu ứng ở mọi nơi, không tôn trọng giảm chuyển động | giữ vài chỗ có nghĩa, thêm `prefers-reduced-motion` |
| Truy cập | không focus ring, thiếu `alt`, nút là `div` | focus rõ, `alt`, đúng thẻ ngữ nghĩa |

## Quy tắc

- Không đổi tên class, id, `data-*` mà test hoặc JS đang bám vào, trừ khi cập nhật cùng chỗ đó.
- Không thêm thư viện UI mới chỉ để đổi giao diện. Dùng CSS sẵn có của dự án.
- Giữ nội dung gốc; đề xuất sửa chữ ở danh sách riêng, không tự sửa.
- Dừng và hỏi khi thay đổi cần quyết định thương hiệu (logo, màu chủ đạo).

## Bước kế

Xong → `/qc-code`, rồi `/verify-before-commit`.
