---
name: tour-guide
description: Thêm product tour (lớp tối với ô spotlight quanh từng phần tử, tooltip nhãn) tự viết, không dùng thư viện. Gọi khi user nói "tour guide", "onboarding tour", "hướng dẫn trong app", "spotlight tour", "walkthrough", hoặc /tour-guide. Hợp React hoặc Next.js với Tailwind; ý tưởng dùng được cho JS thuần.
---

# tour-guide — tour spotlight tự viết

## Ý tưởng

- Phần tử cần chú ý được đánh dấu bằng thuộc tính ổn định `data-tour="tên"`.
- Mỗi route khai báo danh sách điểm dừng (`spots`): `{ target, label, side }`.
- Overlay là một `div` cố định phủ màn hình. Ô spotlight là một `div` đặt tại `getBoundingClientRect()` của target, dùng `box-shadow: 0 0 0 9999px rgba(0,0,0,.6)` để tối phần còn lại.
- Chạm hoặc nhấn bất kỳ đâu → đóng (hoặc sang bước kế nếu muốn nhiều bước).

## Mã (React, rút gọn)

```tsx
type Spot = { target: string; label: string };
export function Tour({ spots, onClose }: { spots: Spot[]; onClose: () => void }) {
  const [rects, setRects] = useState<(DOMRect | null)[]>([]);
  const measure = useCallback(() => {
    setRects(spots.map(s => document.querySelector(`[data-tour="${s.target}"]`)?.getBoundingClientRect() ?? null));
  }, [spots]);

  useLayoutEffect(() => {
    measure();
    const prev = document.documentElement.style.overflow;
    document.documentElement.style.overflow = 'hidden';
    addEventListener('resize', measure);
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    addEventListener('keydown', esc);
    return () => { document.documentElement.style.overflow = prev; removeEventListener('resize', measure); removeEventListener('keydown', esc); };
  }, [measure, onClose]);

  return (
    <div role="dialog" aria-modal="true" aria-label="Hướng dẫn" onClick={onClose} className="fixed inset-0 z-[1000]">
      {rects.map((r, i) => r && (
        <div key={i} className="absolute rounded-lg pointer-events-none"
             style={{ left: r.left - 6, top: r.top - 6, width: r.width + 12, height: r.height + 12, boxShadow: i === 0 ? '0 0 0 9999px rgba(0,0,0,.6)' : '0 0 0 2px #fff' }}>
          <span className="absolute left-0 top-full mt-2 whitespace-nowrap rounded bg-white px-2 py-1 text-sm text-black">{spots[i].label}</span>
        </div>
      ))}
      <p className="absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full bg-white/90 px-4 py-2 text-sm text-black">Chạm để đóng</p>
    </div>
  );
}
```

Chỉ spotlight đầu có `box-shadow` phủ tối; các ô còn lại viền sáng. Muốn từng bước một thì giữ chỉ số bước, chỉ hiển thị một ô.

## Quy tắc

- Đo lại khi `resize` và sau khi bố cục ổn định; không dùng toạ độ cố định.
- Khoá cuộn lúc tour mở, trả lại giá trị cũ khi đóng.
- Có `Esc`, `role="dialog"`, `aria-modal`; trả focus về nút gọi tour khi đóng.
- Hiện một lần mỗi người dùng: lưu cờ trong `localStorage` bọc try/catch.
- Phần tử bị che hoặc không tồn tại (`null`) → bỏ qua điểm dừng, không lỗi.
- Tooltip tránh tràn mép: nếu `r.bottom + chiều cao > innerHeight` thì đặt phía trên.

## Bước kế

`/playwright-verify` ở 360 px và 1280 px: chụp tour mở, kiểm không che nút chính.
