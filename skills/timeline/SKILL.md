---
name: timeline
description: Component timeline dọc bằng HTML, CSS, JS thuần cho changelog, lịch sử, roadmap hoặc lưu trữ bài viết. Mốc theo ngày, hiện dần khi cuộn, đổi bố cục ở 768 px. Gọi khi user nói "làm timeline", "dòng thời gian", "changelog dạng timeline", "roadmap timeline", hoặc /timeline. Sơ đồ nhiều nút quan hệ thì không dùng skill này.
---

# timeline — mốc thời gian dọc

## Cấu trúc

Danh sách có thứ tự `<ol>`; mỗi mốc là `<li>` chứa ngày (`<time datetime>`), tiêu đề, mô tả. Trục dọc vẽ bằng `::before`. Mobile: trục bên trái. Từ 768 px: trục giữa, mốc xen kẽ hai bên.

```html
<ol class="tl">
  <li class="tl__item"><time datetime="2026-11-27">27/11/2026</time><h3>Tiêu đề</h3><p>Mô tả ngắn.</p></li>
</ol>
```

```css
.tl { --line: color-mix(in srgb, currentColor 25%, transparent); list-style: none; margin: 0; padding: 0 0 0 1.5rem; position: relative; }
.tl::before { content: ""; position: absolute; left: .45rem; top: 0; bottom: 0; width: 2px; background: var(--line); }
.tl__item { position: relative; padding: 0 0 2rem 1rem; opacity: 0; translate: 0 1rem; transition: opacity .5s, translate .5s; }
.tl__item::before { content: ""; position: absolute; left: -1.5rem; top: .35rem; width: .75rem; height: .75rem; border-radius: 50%; background: currentColor; }
.tl__item.is-in { opacity: 1; translate: 0 0; }
.tl__item time { font-size: .85rem; opacity: .7; }

@media (min-width: 768px) {
  .tl { padding: 0; }
  .tl::before { left: 50%; translate: -50% 0; }
  .tl__item { width: 50%; padding: 0 2.5rem 2.5rem 0; text-align: right; }
  .tl__item:nth-child(even) { margin-left: 50%; padding: 0 0 2.5rem 2.5rem; text-align: left; }
  .tl__item::before { left: auto; right: -.375rem; }
  .tl__item:nth-child(even)::before { right: auto; left: -.375rem; }
}

@media (prefers-reduced-motion: reduce) { .tl__item { opacity: 1; translate: none; transition: none; } }
```

```js
const io = new IntersectionObserver((es) => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } }), { threshold: 0.2 });
document.querySelectorAll('.tl__item').forEach(el => io.observe(el));
```

## Quy tắc

- Sắp xếp mới nhất lên đầu cho changelog, cũ nhất lên đầu cho lịch sử; chọn một và ghi rõ.
- Không JS thì phải đọc được: đặt `.tl__item` hiện sẵn trong `<noscript><style>` hoặc chỉ ẩn khi `html.js`.
- Ngày dùng `<time datetime>` ISO; hiển thị theo ngôn ngữ trang.
- Dữ liệu từ file JSON/Markdown có thể dựng bằng vòng lặp ở bước build; không nhồi nội dung vào JS.

## Bước kế

`/playwright-verify` ở 360 px và 1280 px.
