---
name: lenis-smooth-scroll
description: Cài Lenis (cuộn mượt theo vật lý) cho toàn trang và đồng bộ đúng với GSAP ScrollTrigger (một vòng raf chung, không lệch pha). Gọi khi user nói "lenis", "smooth scroll", "cuộn mượt", "lenis gsap", hoặc /lenis-smooth-scroll.
---

# lenis-smooth-scroll — Lenis + GSAP chạy chung một nhịp

## Cài

```bash
pnpm add lenis gsap
```

## Mã

```js
import Lenis from 'lenis';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
gsap.registerPlugin(ScrollTrigger);

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduce) {
  const lenis = new Lenis({ autoRaf: false, lerp: 0.1, smoothWheel: true });
  lenis.on('scroll', ScrollTrigger.update);                 // ScrollTrigger đọc vị trí từ Lenis
  gsap.ticker.add((t) => lenis.raf(t * 1000));              // GSAP là driver duy nhất
  gsap.ticker.lagSmoothing(0);                              // không bù trễ, tránh giật khi quay lại tab
}
```

```css
html.lenis, html.lenis body { height: auto; }
.lenis.lenis-smooth { scroll-behavior: auto !important; }
.lenis.lenis-stopped { overflow: hidden; }
[data-lenis-prevent] { overscroll-behavior: contain; }
```

## Quy tắc

1. Chỉ một vòng raf. Có GSAP thì `autoRaf: false` và cho `gsap.ticker` gọi `lenis.raf`. Không có GSAP thì để `autoRaf: true`.
2. Giảm chuyển động (`prefers-reduced-motion`) → không khởi tạo Lenis.
3. Cuộn đến neo: `lenis.scrollTo('#id', { offset: -80 })`, đừng dùng `scrollIntoView`.
4. Vùng cuộn lồng (modal, danh sách) thêm `data-lenis-prevent`.
5. Mở modal: `lenis.stop()`; đóng: `lenis.start()`.
6. SPA: `lenis.destroy()` khi gỡ trang, tạo lại khi vào.

## Cạm bẫy

- Hai nguồn cuộn (Lenis + `scroll-behavior: smooth` CSS) chồng nhau gây giật: xoá cái thứ hai.
- ScrollTrigger tạo trước Lenis sẽ đo sai: khởi tạo Lenis trước, rồi `ScrollTrigger.refresh()`.
- `position: sticky` bên trong container `overflow` khác `visible` sẽ hỏng.

## Bước kế

Ghim và cuộn ngang → `gsap-scrolltrigger-pin`. Verify bằng `/playwright-verify`.
