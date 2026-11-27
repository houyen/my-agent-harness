---
name: wayfinder
disable-model-invocation: true
description: >-
  Lập bản đồ cho một chunk việc QUÁ LỚN với một phiên agent và còn MÙ MỜ — dựng bản đồ các ticket QUYẾT ĐỊNH
  (GitHub issues qua gh, hoặc file markdown khi repo không có GitHub), rồi giải từng ticket một cho tới khi
  đường tới đích rõ. Gọi bằng tay, TRƯỚC cả /propose.
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "2.0.0-personal"
  origin: "mattpocock/skills wayfinder qua rheinmir/setup 1.0.0; tái chế 2026-11-27 thay ledger/frontier.py bằng gh issue hoặc file markdown"
---

# Wayfinder — tìm đường, không lao vào đích

Một ý tưởng lớn, quá lớn cho một phiên, bọc trong sương. Wayfinding là tìm ĐƯỜNG, không phải làm. Mỗi ticket là *một câu hỏi mà lời giải là một quyết định*, không phải một lát build. Bản đồ xong khi không còn gì phải quyết → bàn giao `/propose`.

## Nguyên lý
- **Plan, don't do** — sinh quyết định, không sinh deliverable. Muốn nhảy vào làm = tới mép bản đồ.
- **Một ticket một phiên** (trừ research). **Claim trước khi làm.**
- **Gọi bằng TÊN**, không bằng id trần.
- **Fog of war** — đừng vẽ cái chưa thấy. Câu hỏi đã sắc → ticket (kể cả bị chặn). Chưa phát biểu sắc được → để ở "Chưa xác định".
- **Ngoài phạm vi** — việc vượt đích: đóng, ghi một dòng, không bao giờ tốt nghiệp.
- **HITL không tự trả lời** — ticket cần người thì agent không đứng thay phía người.

## Bốn kiểu ticket
- **research** (AFK) — tra tài liệu/API/web lấy một fact; giải bằng subagent hoặc `web-crawl`.
- **prototype** (HITL) — bản thô (outline, stub, UI) để người phản ứng.
- **grilling** (HITL, mặc định) — hỏi từng câu một, mỗi câu kèm phương án khuyến nghị.
- **task** (HITL/AFK) — việc tay phải xong để mở khoá một quyết định (cấp quyền, đăng ký dịch vụ).

## Nơi lưu bản đồ
1. **Repo có GitHub remote và `gh` đăng nhập** → GitHub issues:
   - Bản đồ: issue nhãn `wayfinder:map`. Ticket: issue nhãn `wayfinder:ticket` + `wayfinder:<kiểu>`, body có dòng `Map: #<map>` và `Blocked by: #a, #b`.
   - Frontier = ticket mở có mọi `Blocked by` đã đóng: `gh issue list -l wayfinder:ticket --state open --json number,title,body` rồi lọc.
   - Claim = comment `đang làm — phiên <mô tả>`; ticket có claim trong 24 giờ thì không nhận. Repo có quy ước claim riêng → theo repo.
   - Tạo nhãn khi chưa có: `gh label create wayfinder:map` (hỏi user trước lần đầu, vì là thao tác ra ngoài).
2. **Không có GitHub** → `docs/wayfinder/<tên-map>.md`, mỗi ticket là một mục `### T-NN <tên>` có `Kiểu`, `Blocked by`, `Claim`, `Trạng thái`, `Lời giải`.

Thân bản đồ:
```markdown
## Đích
<đi tới cuối bản đồ trông thế nào — 1–2 dòng>
## Quyết định đã có
- [<tên ticket>](link) — <gist một dòng>
## Chưa xác định
<sương trong phạm vi, chưa thành ticket>
## Ngoài phạm vi
<việc loại khỏi đích này>
```

## HOW
### Chart (dựng bản đồ) — user đưa ý tưởng
1. Grill để chốt **Đích** một câu.
2. Grill theo bề rộng để lộ frontier: quyết định mở + bước đầu làm được. Không có sương nào → không cần bản đồ, dừng và hỏi user đi tiếp thế nào.
3. Tạo bản đồ + các ticket ghim được; nối `Blocked by` ở lượt hai (cần id trước).
4. Ticket research → subagent song song, ghi phát hiện vào ticket.
5. Dừng. Dựng bản đồ là việc của một phiên.

### Work (làm qua bản đồ) — user đưa bản đồ
1. Nạp bản đồ (thân map, không nạp mọi ticket).
2. Chọn ticket user nêu, hoặc ticket frontier đầu tiên. Claim trước.
3. Giải; HITL thì hỏi người sống.
4. Ghi lời giải vào ticket, đóng, thêm một dòng vào "Quyết định đã có".
5. Thêm ticket mới lộ ra, tốt nghiệp sương đã ghim được, loại việc ngoài phạm vi, sửa ticket bị lời giải phủ định.
6. Không còn gì phải quyết → bàn giao `/propose`.
