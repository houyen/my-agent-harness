---
name: svg-stroke-reveal
description: Vẽ dần nét SVG theo tiến độ cuộn hoặc khi vào khung nhìn (stroke-dasharray và stroke-dashoffset, đo bằng getTotalLength). Gọi khi user nói "vẽ svg khi cuộn", "svg stroke draw", "logo vẽ dần", "path animation", "stroke-dashoffset", hoặc /svg-stroke-reveal.
---

# svg-stroke-reveal — nét SVG vẽ dần

## Nguyên lý

Với `<path>` dài `L`: đặt `stroke-dasharray: L` (một nét dài bằng cả đường) và `stroke-dashoffset: L` (đẩy nét ra ngoài, nên ẩn). Giảm offset về 0 thì đường hiện dần.

## Theo cuộn

```html
<svg viewBox="0 0 400 200" aria-hidden="true"><path class="draw" d="M10 150 C 100 10, 200 190, 390 40" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>
```

```js
const path = document.querySelector('.draw');
const L = path.getTotalLength();
path.style.strokeDasharray = L;
path.style.strokeDashoffset = L;

const host = path.closest('svg');
let raf = 0;
function update() {
  raf = 0;
  const r = host.getBoundingClientRect();
  const p = Math.min(1, Math.max(0, (innerHeight - r.top) / (innerHeight + r.height)));
  path.style.strokeDashoffset = L * (1 - p);
}
addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(update); }, { passive: true });
update();
```

## Một lần khi vào khung nhìn

```css
.draw { transition: stroke-dashoffset 1.2s ease; }
```

```js
new IntersectionObserver((es, io) => es.forEach(e => {
  if (e.isIntersecting) { e.target.style.strokeDashoffset = 0; io.unobserve(e.target); }
}), { threshold: 0.4 }).observe(path);
```

## Quy tắc

- Đo `getTotalLength()` sau khi SVG có trong DOM; tính lại khi đổi kích thước nếu dùng `vector-effect` hoặc scale.
- Nhiều path: dùng độ trễ `transition-delay` tăng dần hoặc chia nhỏ tiến độ cho từng path.
- Giảm chuyển động: đặt `stroke-dashoffset: 0` ngay, không animate.
- Chỉ dùng cho path có `stroke`. Hình tô (`fill`) cần thêm `fill-opacity` chuyển ở cuối.
- Nếu không có JS, nét phải vẫn hiện: thêm `<noscript><style>.draw{stroke-dashoffset:0!important}</style></noscript>`.

## Cạm bẫy

- `<line>`, `<circle>`, `<rect>` cũng có `getTotalLength()`; `<g>` thì không.
- `stroke-linecap: round` để lại chấm nhỏ ở điểm bắt đầu khi offset gần bằng `L`: đặt offset `L + 1`.

## Bước kế

`/playwright-verify`: chụp ảnh ở 0%, 50%, 100% cuộn.
