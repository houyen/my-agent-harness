---
name: mask-reveal-transition
description: Lộ ảnh qua mask CSS hữu cơ (vòng loang mực, mask-image radial-gradient theo tiến độ cuộn) hoặc pin split-screen (ảnh cố định bên trái, chữ cuộn bên phải, đổi ảnh bằng mask). Gọi khi user nói "mask reveal", "loang mực", "ink reveal", "chuyển ảnh bằng mask", "split screen sticky", hoặc /mask-reveal-transition.
---

# mask-reveal-transition — lộ ảnh bằng mask CSS

CSS thuần cộng một đoạn JS nhỏ cập nhật biến. Không WebGL, không canvas.

## Mẫu 1: vòng loang theo tiến độ

Hai ảnh chồng nhau; ảnh trên bị mask bằng `radial-gradient` có bán kính theo biến `--p` (0 đến 100).

```css
.reveal { position: relative; height: 100vh; }
.reveal img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.reveal .top {
  --p: 0;
  mask-image: radial-gradient(circle at 50% 50%, #000 calc(var(--p) * 1%), transparent calc(var(--p) * 1% + 12%));
  -webkit-mask-image: radial-gradient(circle at 50% 50%, #000 calc(var(--p) * 1%), transparent calc(var(--p) * 1% + 12%));
}
```

```js
const el = document.querySelector('.reveal'), top = el.querySelector('.top');
let ticking = false;
addEventListener('scroll', () => {
  if (ticking) return; ticking = true;
  requestAnimationFrame(() => {
    const r = el.getBoundingClientRect();
    const p = Math.min(1, Math.max(0, -r.top / (r.height - innerHeight)));
    top.style.setProperty('--p', (p * 110).toFixed(2));   // 110 để vòng phủ kín góc
    ticking = false;
  });
}, { passive: true });
```

Khung cần cao hơn màn hình (ví dụ `height: 250vh`) và bên trong dùng `position: sticky; top: 0; height: 100vh`.

## Mẫu 2: split-screen ghim

Cột trái `position: sticky; top: 0; height: 100vh` chứa ngăn xếp ảnh. Cột phải là các đoạn chữ cao 100vh. `IntersectionObserver` (ngưỡng 0.6) đặt `data-active` cho đoạn đang xem; ảnh tương ứng nhận class `.on` để mask mở ra (`--p` chuyển 0 → 110 bằng `transition` qua `@property`).

```css
@property --p { syntax: '<number>'; inherits: false; initial-value: 0; }
.stack img { transition: --p .9s ease; }
.stack img.on { --p: 110; }
```

## Quy tắc

- Luôn có tiền tố `-webkit-mask-image` song song bản chuẩn.
- Tắt chuyển động khi `prefers-reduced-motion: reduce`: hiện ảnh đích ngay.
- Ảnh có `alt` rõ; chữ không nằm trong ảnh.
- Ảnh cùng tỷ lệ để mask không lộ viền.

## Cạm bẫy

- Chỉ animate biến CSS trên một phần tử: nhiều lớp mask lớn làm tụt FPS ở màn hình 4K.
- Cha có `overflow: hidden` làm `sticky` ngừng hoạt động.

## Bước kế

`/playwright-verify`: chụp ảnh ở `--p` = 0, 55, 110.
