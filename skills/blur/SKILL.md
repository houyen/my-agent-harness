---
name: blur
description: Chuyển ảnh toàn màn hình bằng WebGL "zoom blur" (Three.js + fragment shader tự viết, parallax theo chuột). Dùng cho hero hoặc slideshow ảnh. Gọi khi user nói "hiệu ứng blur ảnh", "chuyển ảnh zoom blur", "hero WebGL", "slideshow shader", hoặc /blur. Nặng GPU: không dùng cho hiệu ứng cuộn thường (dùng scroll-effects).
---

# blur — chuyển ảnh zoom blur (WebGL)

Bản viết lại độc lập cho repo này. Không có asset đi kèm: đoạn mã dưới đây là toàn bộ cơ chế.

## Khi nào dùng

- Hero hoặc slideshow ảnh toàn màn hình, 3 đến 8 ảnh, có người thật xem trên màn hình lớn.
- Không dùng khi trang đã nặng, khi cần chạy tốt trên máy yếu, hoặc chỉ cần hiệu ứng cuộn nhẹ → `scroll-effects`.

## Cơ chế

1. Một `PlaneGeometry(2, 2)` phủ kín clip space, `ShaderMaterial` với hai texture `uFrom`, `uTo` và `uProgress` từ 0 đến 1.
2. Fragment shader lấy mẫu mỗi texture nhiều lần dọc theo vector từ tâm tới điểm ảnh (radial blur). Độ mờ lớn nhất ở giữa quá trình (`sin(pi * p)`), rồi trộn `uFrom` sang `uTo`.
3. Chuột dịch tâm blur và UV một chút (parallax), nội suy mượt bằng lerp mỗi frame.

```glsl
uniform sampler2D uFrom, uTo;
uniform float uProgress;      // 0..1
uniform vec2 uMouse;          // -0.5..0.5
varying vec2 vUv;
const int TAPS = 12;

vec4 radial(sampler2D t, vec2 uv, vec2 c, float amt) {
  vec4 sum = vec4(0.0);
  for (int i = 0; i < TAPS; i++) {
    float k = float(i) / float(TAPS - 1);
    sum += texture2D(t, uv + (c - uv) * k * amt);
  }
  return sum / float(TAPS);
}

void main() {
  vec2 c = vec2(0.5) + uMouse * 0.1;
  float amt = sin(3.14159265 * uProgress) * 0.35;
  vec2 uv = vUv + uMouse * 0.02;
  gl_FragColor = mix(radial(uFrom, uv, c, amt), radial(uTo, uv, c, amt), smoothstep(0.0, 1.0, uProgress));
}
```

```js
const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
// tween uProgress bằng gsap.to(material.uniforms.uProgress, { value: 1, duration: 1.2, ease: 'power2.inOut' })
```

## Quy tắc

- `prefers-reduced-motion: reduce` → đổi ảnh bằng crossfade CSS, không khởi tạo WebGL.
- Texture dùng `colorSpace = SRGBColorSpace`, kích thước luỹ thừa 2 không bắt buộc nhưng đặt `generateMipmaps = false` nếu `minFilter = LinearFilter`.
- Chỉ render khi đang chuyển hoặc chuột đang di (dừng `requestAnimationFrame` lúc rảnh).
- Giải phóng `texture.dispose()`, `material.dispose()`, `renderer.dispose()` khi gỡ component.
- Có ảnh dự phòng `<img>` trong HTML cho trường hợp không có WebGL.

## Cạm bẫy

- Ảnh khác tỷ lệ màn hình: tự tính `uvScale` kiểu "cover", đừng kéo giãn.
- Vòng lặp `TAPS` phải là hằng số biên dịch được (GLSL ES 1.0).
- Safari iOS giới hạn kích thước canvas: ép `setPixelRatio(1.5)` nếu thấy giật.

## Bước kế

Kiểm bằng `/playwright-verify`: chụp ảnh ở progress 0, 0.5, 1 và đo FPS thấp nhất.
