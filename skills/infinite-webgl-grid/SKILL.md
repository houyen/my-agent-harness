---
name: infinite-webgl-grid
description: Lưới ảnh WebGL (Three.js) kéo hoặc cuộn vô hạn mọi hướng bằng coordinate wrapping (modulo), chỉ cần N×N tile thật. Gọi khi user nói "lưới ảnh vô hạn", "infinite grid", "kéo ảnh WebGL", "gallery vô hạn", hoặc /infinite-webgl-grid.
---

# infinite-webgl-grid — lưới vô hạn bằng modulo

## Ý tưởng

Không tạo vô hạn mesh. Tạo N×N tile (ví dụ 5×5) rộng `W` tổng. Giữ một offset ảo `(ox, oy)` do kéo/cuộn cộng dồn. Mỗi frame, vị trí tile `(i, j)` được tính lại và "quấn" (wrap) vào khoảng quanh camera bằng modulo, nên lưới trông vô hạn.

## Lõi

```js
const N = 5, TILE = 2, GAP = 0.2, STEP = TILE + GAP, SPAN = N * STEP;
const wrap = (v, span) => ((v % span) + span) % span;       // modulo luôn dương

function layout(offset) {
  tiles.forEach(({ mesh, i, j }) => {
    const x = wrap(i * STEP + offset.x + SPAN / 2, SPAN) - SPAN / 2;
    const y = wrap(j * STEP + offset.y + SPAN / 2, SPAN) - SPAN / 2;
    mesh.position.set(x, y, 0);
  });
}
```

```js
// kéo: cộng dồn delta theo đơn vị thế giới, thêm quán tính
const vel = new THREE.Vector2(), offset = new THREE.Vector2();
addEventListener('pointermove', (e) => { if (!dragging) return; vel.set(e.movementX, -e.movementY).multiplyScalar(unitsPerPx); });
function tick() { offset.add(vel); vel.multiplyScalar(0.92); layout(offset); renderer.render(scene, cam); requestAnimationFrame(tick); }
```

## Quy tắc

- Chọn `SPAN` lớn hơn vùng nhìn thấy (khung camera) ít nhất một tile, nếu không sẽ thấy khoảng trống ở rìa.
- Texture: nạp ảnh một lần, dùng lại cho tile bằng `(i + j * N) % imageCount`.
- Tile dùng chung một `PlaneGeometry` và `MeshBasicMaterial` riêng theo texture (hoặc một `InstancedMesh` nếu N lớn).
- Bật `wheel` → cộng vào `vel` (có `preventDefault`, đăng ký `{ passive: false }`).
- `prefers-reduced-motion`: bỏ quán tính, dùng bước nhảy ngắn.
- Dọn dẹp: `dispose()` geometry, material, texture, renderer khi gỡ.

## Cạm bẫy

- `%` của JS trả số âm: luôn dùng `wrap` ở trên.
- Pixel ratio cao làm nặng: giới hạn `Math.min(devicePixelRatio, 2)`.
- Chạm trên điện thoại: đặt `touch-action: none` cho canvas.
- Có chi tiết dưới tile cần nhấp (click): dùng `Raycaster` với vị trí đã wrap.

## Bước kế

`/playwright-verify`: kéo một đoạn dài theo cả bốn hướng, xác nhận không có khoảng trống.
