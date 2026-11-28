---
name: threejs-particle-morph
description: Đám hạt Three.js (THREE.Points + BufferGeometry) hội tụ từ vị trí ngẫu nhiên thành ảnh hoặc logo theo tiến độ cuộn, lấy mẫu pixel từ canvas ẩn làm toạ độ đích. Gọi khi user nói "particle image", "hạt hội tụ thành logo", "three.js particle scroll", "particle morph", hoặc /threejs-particle-morph.
---

# threejs-particle-morph — hạt hội tụ thành ảnh

## Các bước

1. **Lấy toạ độ đích từ ảnh**: vẽ ảnh lên canvas nhỏ (khoảng 160 px cạnh dài), đọc `getImageData`, giữ điểm có alpha và độ sáng đủ ngưỡng. Mỗi điểm cho một hạt: vị trí đích `(x, y, 0)` và màu.
2. **Vị trí xuất phát**: ngẫu nhiên trong một khối lớn quanh cảnh.
3. **Mỗi frame**: `pos = lerp(start, target, easeOut(progress))`, `progress` lấy từ tiến độ cuộn của phần tử chứa canvas.

```js
function sample(img, W = 160, threshold = 40) {
  const c = document.createElement('canvas');
  const s = W / Math.max(img.width, img.height);
  c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, c.width, c.height);
  const { data } = ctx.getImageData(0, 0, c.width, c.height);
  const pts = [], cols = [];
  for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
    const i = (y * c.width + x) * 4;
    if (data[i + 3] > 128 && (data[i] + data[i + 1] + data[i + 2]) / 3 > threshold) {
      pts.push((x - c.width / 2) / 20, (c.height / 2 - y) / 20, 0);
      cols.push(data[i] / 255, data[i + 1] / 255, data[i + 2] / 255);
    }
  }
  return { pts: new Float32Array(pts), cols: new Float32Array(cols) };
}

const { pts: target, cols } = sample(img);
const n = target.length / 3;
const start = Float32Array.from({ length: n * 3 }, () => (Math.random() - 0.5) * 30);
const pos = start.slice();
const geo = new THREE.BufferGeometry();
geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
geo.setAttribute('color', new THREE.BufferAttribute(cols, 3));
const points = new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.08, vertexColors: true, sizeAttenuation: true }));
scene.add(points);

const ease = (t) => 1 - Math.pow(1 - t, 3);
function update(p) {
  const e = ease(p);
  for (let i = 0; i < pos.length; i++) pos[i] = start[i] + (target[i] - start[i]) * e;
  geo.attributes.position.needsUpdate = true;
}
```

## Quy tắc

- Ảnh cùng nguồn gốc (hoặc có CORS) để `getImageData` không bị chặn (canvas "tainted").
- Giới hạn số hạt (khoảng 30 nghìn trở xuống); giảm `W` trên điện thoại.
- Với số hạt lớn, chuyển phép lerp sang vertex shader với `uniform float uProgress` thay vì cập nhật mảng bằng CPU.
- Giảm chuyển động: hiện ngay trạng thái đích.
- Dọn dẹp `geometry.dispose()`, `material.dispose()`, `renderer.dispose()` khi gỡ.

## Cạm bẫy

- Trục Y của canvas hướng xuống, của Three.js hướng lên: đã đảo trong `sample`.
- Logo nền trong suốt cho kết quả sạch nhất; ảnh ảnh chụp cần ngưỡng sáng điều chỉnh.

## Bước kế

`/playwright-verify`: chụp ở tiến độ 0, 0.5, 1 và kiểm số hạt hiển thị.
