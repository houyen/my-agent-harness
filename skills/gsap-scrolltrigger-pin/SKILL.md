---
name: gsap-scrolltrigger-pin
description: Ghim một section khi cuộn tới và đổi cuộn dọc thành trượt ngang qua GSAP ScrollTrigger (pin, scrub, xPercent của track). Gọi khi user nói "gsap scrolltrigger", "pin section", "cuộn ngang", "horizontal scroll section", hoặc /gsap-scrolltrigger-pin.
---

# gsap-scrolltrigger-pin — cuộn dọc thành trượt ngang

## Cơ chế

Một `section` bị ghim (`pin`). Bên trong là `track` nằm ngang chứa N slide. Tween dịch `track` sang trái đúng bằng phần dư chiều rộng, tiến độ gắn với vị trí cuộn (`scrub`). Chiều cao cuộn (`end`) bằng độ dài track.

## Mã

```html
<section class="hs"><div class="hs__track"><article class="hs__slide">…</article>…</div></section>
```

```css
.hs { overflow: hidden; }
.hs__track { display: flex; width: max-content; }
.hs__slide { flex: 0 0 100vw; min-height: 100vh; }
```

```js
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
gsap.registerPlugin(ScrollTrigger);

const mm = gsap.matchMedia();
mm.add('(min-width: 768px) and (prefers-reduced-motion: no-preference)', () => {
  const track = document.querySelector('.hs__track');
  const dist = () => track.scrollWidth - innerWidth;
  gsap.to(track, {
    x: () => -dist(),
    ease: 'none',
    scrollTrigger: {
      trigger: '.hs',
      pin: true,
      scrub: 1,
      start: 'top top',
      end: () => '+=' + dist(),
      invalidateOnRefresh: true,
      anticipatePin: 1,
    },
  });
});
```

## Quy tắc

- Dùng `gsap.matchMedia()`: trên màn hình hẹp hoặc `prefers-reduced-motion: reduce` thì để các slide xếp dọc bình thường.
- Giá trị phụ thuộc kích thước viết dạng hàm (`x: () => …`) và bật `invalidateOnRefresh`, để resize tính lại.
- `ease: 'none'` cho tween gắn `scrub`; easing làm lệch tiến độ.
- Không bọc phần tử ghim trong cha có `transform`; pin dùng `position: fixed` và sẽ vỡ.
- Có Lenis thì đồng bộ theo `lenis-smooth-scroll`; đừng chạy hai vòng raf.

## Cạm bẫy

- Ảnh tải chậm đổi `scrollWidth`: gọi `ScrollTrigger.refresh()` sau khi ảnh tải xong.
- Thêm nhiều ScrollTrigger phía dưới phần ghim phải tạo sau nó (thứ tự tạo quyết định tính `start`).
- Thanh cuộn ngang bất ngờ: kiểm `body` không `overflow-x` do `100vw` cộng thanh cuộn dọc.

## Bước kế

`/playwright-verify`: cuộn tới 0%, 50%, 100% của đoạn ghim và chụp ảnh.
