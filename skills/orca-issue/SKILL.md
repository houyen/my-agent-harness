---
name: orca-issue
description: Vòng xử lý SỰ CỐ repro-first — bug, lỗi runtime, regression, hành vi sai, incident. Triage → repro ĐỎ (chưa tái hiện thì chưa sửa) → khoanh vùng root cause → fix surgical đỏ→xanh → ghi bài học. Gọi khi user nói "/orca-issue", "xử lý sự cố", "debug kỹ", "lỗi này tái diễn".
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "2.0.0-personal"
  origin: "rheinmir/setup orca-issue 1.0.0 (+ obra/superpowers systematic-debugging), tái chế 2026-11-27 bỏ llmwiki/failure-flywheel/problem-tree"
---

# Skill: orca-issue — vòng xử lý sự cố

Hai chốt cứng: **không tái hiện được thì không sửa**; **repro chưa xanh thì không đóng**.

## Rules
- **Đọc lỗi NGUYÊN VĂN trước khi đoán** — error message + stack trace là dữ kiện rẻ nhất.
- **Không repro, không sửa** — mọi fix truy về một bằng chứng đỏ đã lưu.
- **Không xanh, không đóng** — lời agent không phải bằng chứng.
- **Một giả thuyết một lần** — mỗi vòng đổi MỘT thứ rồi chạy lại repro.
- **3 fix liên tiếp thất bại → dừng**, nghi sai tầng/sai component/sai giả định nền; không thử fix thứ 4 cùng cỡ.
- **Surgical** — chỉ chạm vùng đã khoanh; code lân cận "muốn dọn" thì ghi chú, không dọn.
- **Tương xứng** — lỗi hiển nhiên một dòng (typo, import thiếu) không cần đủ nghi thức; vẫn phải chạy lại để thấy xanh.

## HOW
1. **Triage** — chép triệu chứng 1–2 câu (cái gì sai, ở đâu, từ bao giờ), trích lỗi nguyên văn, phân mức (chặn việc / khó chịu / thẩm mỹ). Chưa rõ → hỏi user.
2. **Repro ĐỎ** — test hoặc script tái hiện, chạy ra FAIL, giữ lệnh + output làm bằng chứng. Đặt test theo cấu trúc test của repo; script tạm để scratchpad. Không tái hiện được (flaky) → ghi điều kiện đã thử, thêm log/probe, không sửa mò.
3. **Khoanh vùng** — `impact-check` cho vùng nghi vấn; `git log -S`/`git bisect` khi nghi regression theo thời gian; đọc code thật. Kết quả một câu: "root cause nằm ở X vì Y".
4. **Fix đỏ→xanh** — sửa qua `safe-change` nếu đụng code dùng chung. Chạy lại repro: phải XANH. Chạy gate repo, rồi `verify-before-commit`.
5. **Ghi bài học** (sau commit):
   - Commit message nêu triệu chứng + root cause.
   - Repo có nơi ghi sự cố/trạng thái (`docs/STATUS.md`, `docs/reports/…`, issue tracker) → ghi ngắn ở đó theo quy ước repo.
   - Lỗi có tính lặp lại hoặc bẫy không hiển nhiên → lưu memory `feedback`/`project` kèm **Why**.

## Failure boundaries
- Triệu chứng chưa rõ → clarify.
- Repro còn đỏ sau fix → quay lại bước 3.
- User xin tính năng mới, không phải sự cố → chuyển `/propose`.
