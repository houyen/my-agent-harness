---
name: css-scroll-driven-native
description: Hiệu ứng cuộn trang bằng CSS thuần (animation-timeline scroll() và view(), animation-range), không JavaScript. Gọi khi user nói "css scroll driven animation", "animation-timeline", "thanh tiến độ cuộn bằng CSS", "reveal khi cuộn không JS", hoặc /css-scroll-driven-native. Là lớp nâng cấp dần (progressive enhancement), không thay `scroll-effects` khi cần chạy chắc trên mọi trình duyệt.
---

# css-scroll-driven-native — cuộn bằng CSS, không JS

## Khi nào dùng

- Muốn hiệu ứng gắn vào tiến độ cuộn mà không viết JS và không tốn main thread.
- Chấp nhận Firefox và Safari có thể chưa hỗ trợ: trang vẫn phải đọc được khi không có hiệu ứng.
- Cần chạy chắc trên mọi trình duyệt → dùng `scroll-effects` (IntersectionObserver).

## Hai loại timeline

| Timeline | Gắn vào | Dùng cho |
|---|---|---|
| `scroll()` | tiến độ cuộn của một container (mặc định: cha cuộn gần nhất) | thanh tiến độ trang, header co lại |
| `view()` | độ hiện của chính phần tử trong khung nhìn | reveal, parallax theo phần tử |

## Mẫu

```css
@keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes rise { from { opacity: 0; translate: 0 2rem; } to { opacity: 1; translate: 0 0; } }

@supports (animation-timeline: scroll()) {
  .progress {
    position: fixed; inset: 0 0 auto 0; height: 4px;
    transform-origin: 0 50%;
    animation: grow linear both;
    animation-timeline: scroll(root block);
  }
  .reveal {
    animation: rise linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 30%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .progress, .reveal { animation: none; }
}
```

## Quy tắc

1. Đặt toàn bộ trong `@supports (animation-timeline: scroll())`. Ngoài khối này phần tử phải ở trạng thái cuối (đọc được).
2. Dùng `animation-timing-function: linear`: easing làm tiến độ lệch khỏi vị trí cuộn.
3. `animation-fill-mode: both` (viết tắt `both`) để giữ trạng thái đầu và cuối.
4. Phạm vi: `entry`, `exit`, `cover`, `contain`; viết `animation-range: entry 0% cover 40%`.
5. Chỉ animate `transform`, `opacity`, `translate`, `scale`, `filter`. Tránh `width`, `top`.
6. Tắt khi `prefers-reduced-motion: reduce`.

## Cạm bẫy

- Phần tử có `overflow: hidden` ở cha làm `view()` đo theo cha đó, không theo viewport.
- Đặt `animation-timeline` trước shorthand `animation` sẽ bị shorthand ghi đè: viết sau.
- Tên timeline đặt tay (`view-timeline-name`, `timeline-scope`) chỉ cần khi gắn hiệu ứng ở phần tử khác.

## Bước kế

`/playwright-verify` ở Chromium; ghi rõ trong báo cáo trình duyệt nào đã kiểm.
