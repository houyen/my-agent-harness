# So sánh với các harness mã nguồn mở khác

Ngày khảo sát: 2026-11-28. Số liệu lấy từ GitHub API (`gh api repos/<repo>`) và README của từng repo.
Tiêu chí chọn (theo `AGENTS.md`): nhiều sao (ngưỡng 5.000), còn cập nhật, có giấy phép rõ.
Mục "Chưa xác minh" ở cuối liệt kê những gì tôi chưa đọc, đừng coi là kết luận.

## Repo đã đọc README

| Repo | Sao | Giấy phép | Push gần nhất | Bản phát hành mới nhất | Issue mở |
|---|---|---|---|---|---|
| obra/superpowers | 328.742 | MIT | 2026-11-28 | v7.0.2 (2026-11-03) | 377 |
| affaan-m/ECC | 312.175 | MIT | 2026-11-23 | v2.2.3 (2026-10-01) | 244 |
| addyosmani/agent-skills | 120.885 | MIT | 2026-11-24 | 0.6.18 (2026-11-24) | 119 |
| mindfold-ai/Trellis | 15.200 | **AGPL-3.0** | 2026-09-29 | không có release GitHub (phát hành qua npm) | 92 |

## Cách họ làm

**superpowers** (phương pháp luận dạng skill)
- Skill tự kích hoạt từ chỉ dẫn khởi động (`using-superpowers`), người dùng không phải gõ lệnh.
- Dòng làm việc: brainstorm → spec (trình từng đoạn ngắn) → kế hoạch cho "kỹ sư junior không có ngữ cảnh" → `subagent-driven-development` với duyệt hai tầng (đúng spec, rồi chất lượng code).
- Triết lý: TDD, quy trình hơn đoán mò, giảm độ phức tạp, bằng chứng hơn lời khẳng định.
- Phân phối: plugin marketplace và cài riêng cho từng harness (Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Copilot CLI... hơn 15 mục trong README).

**ECC** ("hệ điều hành cho agent harness")
- Tách bạch 5 thứ để không nhồi context: Skills (nạp khi cần), Agents (worker có phạm vi và quyền công cụ riêng), Rules (luôn nạp nên cài có chọn lọc), Hooks (chạy ngoài context của model), Instincts (mẫu học từ phiên thật, có điểm tin cậy).
- Có profile cài đặt `minimal` bỏ hẳn `hooks-runtime`, cho ai muốn ít context và không hook.
- "Memory Vault": một định dạng Markdown cục bộ (`.ecc/memory/`) để bàn giao ngữ cảnh giữa các harness (Claude, Codex, Hermes...).
- Lưu ý chính README ghi: mỗi harness chỉ chọn một đường cài, tránh cài chồng.

**addyosmani/agent-skills** (kỹ năng theo vòng đời)
- 10 lệnh gạch theo vòng đời: `/spec`, `/plan`, `/build`, `/test`, `/review`, `/ship`... mỗi lệnh kích hoạt đúng skill.
- Cài bằng `npx skills add` cho hơn 70 agent, hoặc plugin marketplace.
- Nhược điểm tự ghi trong README (issue #361): cài lẻ từng skill không mang theo thư mục `references/` dùng chung, nên checklist chung bị mất.

**Trellis** (khung kỹ thuật lưu trong repo)
- Lưu spec, task, journal ngay trong repo (`.trellis/spec`, `.trellis/tasks`, `.trellis/workspace`) để phiên sau không bắt đầu từ số 0.
- Vòng 4 pha: Plan → Implement → Verify → Finish; sub-agent riêng cho từng pha; `update-spec` đưa bài học trở lại spec.
- Giấy phép AGPL-3.0: **không sao chép mã hay văn bản vào repo MIT này**; chỉ học ý tưởng.

## So với my-agent-harness

| Hạng mục | Họ | Chúng ta |
|---|---|---|
| Nguồn chân lý luật | rải rác trong skill, hook, rule từng harness | một `policy.yaml`, sinh wiring cho từng vendor |
| Chặn thật (hook) | ECC có hook (README); superpowers chưa kiểm | R20, R22 chặn thật; có audit log và `decisions.jsonl` kèm hash để kiểm lại |
| Xem trước hệ quả | không thấy trong README | `harness-plan` và `harness-replay` |
| Nguồn gốc skill | tuỳ repo | `NOTICE.md` + `SHA256SUMS`, cài offline |
| Phân phối | plugin marketplace, `npx skills` | `install.sh`, `profile.py`; chưa có marketplace |
| Số harness hỗ trợ | 15 đến 70+ | Claude Code đầy đủ, Codex một phần, opencode, CI |
| Agent con (`agents/`) | ECC, Trellis có | chưa có |
| Bộ kiểm skill (evals) | addyosmani có thư mục `evals/` (chưa đọc nội dung) | `test-skills.sh` kiểm cấu trúc, chưa kiểm hành vi |
| Bộ nhớ dự án trong repo | Trellis, ECC | dùng memory của Claude và `orca-handover`, chưa chuẩn hoá |
| Chế độ ít context | ECC `minimal` | chưa có profile không-hook |

## Điều nên học (xếp theo giá trị trên chi phí)

1. **Profile `minimal` không hook** (ECC): thêm cờ cài bỏ hết hook, cho máy hoặc repo muốn ít context. Chi phí thấp.
2. **Duyệt hai tầng** (superpowers): `qc-code` hiện duyệt một lượt; tách "đúng spec chưa" khỏi "code tốt chưa". Chi phí thấp, chỉ sửa một skill.
3. **Thư mục `references/` dùng chung** và cách cài không làm mất nó (bài học issue #361 của addyosmani): nếu thêm tài liệu dùng chung cho nhiều skill, đặt cạnh từng skill hoặc nhân bản, không để ở gốc.
4. **Bộ kiểm skill**: đã làm: `test-skills.sh` kiểm `name` khớp thư mục, có `description`, có dòng trong `NOTICE.md`, checksum khớp. Chưa kiểm chất lượng cụm kích hoạt.
5. **Plugin marketplace** cho Claude Code: nâng độ phủ nhưng tốn bảo trì, chưa cần khi chỉ dùng cá nhân.
6. **Agent con và bộ nhớ trong repo**: chỉ làm khi có nhu cầu thật; hiện `orca-handover` đủ dùng.

## Chưa xác minh

- `langchain-ai/deepagents` (31.648 sao, MIT), `ruvnet/ruflo` (82.579 sao), `HKUDS/OpenHarness` (16.250 sao), `agentsmd/agents.md` (25.743 sao), `anthropics/skills` (201.747 sao, GitHub không ghi giấy phép ở cấp repo): mới đọc thông tin repo, **chưa đọc README hay mã**. Chưa so sánh được.
- `Leonxlnx/taste-skill` (khoảng 122 nghìn sao): chưa kiểm giấy phép; README repo riêng cũ ghi `design-taste-frontend` bắt nguồn từ đây, nên bản trong repo này đã viết lại độc lập.
- Số sao và số issue thay đổi từng ngày; bảng trên đúng tại thời điểm khảo sát.
- Tôi chưa cài hay chạy thử bất kỳ harness nào ở trên; mô tả chỉ dựa vào README.
