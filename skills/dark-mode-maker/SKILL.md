---
name: dark-mode-maker
description: Thêm chế độ sáng/tối có hiệu ứng vòng tròn loang từ vị trí nút bấm (View Transitions API, có đường lui), kèm bảng màu tối trung tính. Gọi khi user nói "dark mode", "chế độ tối", "đổi theme có hiệu ứng", "theme toggle", hoặc /dark-mode-maker.
---

# dark-mode-maker — chuyển sáng/tối có hiệu ứng loang

## Khi nào dùng

Trang cần nút đổi theme: nhớ lựa chọn, theo hệ điều hành khi chưa chọn, không nháy sáng lúc tải.

## Ba phần

### 1. Token màu (không hard-code màu trong component)

```css
:root { color-scheme: light dark; --bg: #ffffff; --fg: #111827; --muted: #6b7280; --line: #e5e7eb; --accent: #2563eb; }
:root[data-theme="dark"] { --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --line: #30363d; --accent: #58a6ff; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --line: #30363d; --accent: #58a6ff; } }
body { background: var(--bg); color: var(--fg); }
```

Tối trung tính: nền xám xanh rất đậm, không dùng đen tuyệt đối `#000`; chữ không trắng tuyệt đối; kiểm tương phản chữ thường ≥ 4.5:1.

### 2. Chặn nháy lúc tải (đặt inline trong `<head>`, trước CSS)

```html
<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>
```

### 3. Nút đổi và hiệu ứng

```js
function applyTheme(next) { document.documentElement.dataset.theme = next; try { localStorage.setItem('theme', next); } catch {} }
function toggle(ev) {
  const dark = document.documentElement.dataset.theme === 'dark' || (!document.documentElement.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
  const next = dark ? 'light' : 'dark';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!document.startViewTransition || reduce) return applyTheme(next);
  const r = ev.currentTarget.getBoundingClientRect();
  const x = ev.clientX || r.left + r.width / 2, y = ev.clientY || r.top + r.height / 2;
  const radius = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
  document.startViewTransition(() => applyTheme(next)).ready.then(() =>
    document.documentElement.animate(
      { clipPath: [`circle(0 at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
      { duration: 500, easing: 'ease-in-out', pseudoElement: '::view-transition-new(root)' }));
}
```

```css
::view-transition-old(root), ::view-transition-new(root) { animation: none; mix-blend-mode: normal; }
```

## Quy tắc

- Nút là `<button aria-pressed>` hoặc `role="switch"` với `aria-checked`, có nhãn chữ cho trình đọc màn hình.
- Không có `startViewTransition` hoặc người dùng bật giảm chuyển động → đổi ngay, không hiệu ứng.
- Ảnh, biểu đồ, bóng đổ cũng phải có biến thể tối (kiểm bằng mắt từng trang chính).

## Cạm bẫy

- `localStorage` có thể ném lỗi (chế độ riêng tư): luôn bọc try/catch.
- Đổi `data-theme` trên `<html>`, không trên `<body>`, để `color-scheme` áp cả thanh cuộn.

## Bước kế

`/playwright-verify`: chụp ảnh hai theme và đo tương phản chữ chính.
