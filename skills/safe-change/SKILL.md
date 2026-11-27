---
name: safe-change
description: Modify shared code without breaking existing callers
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.0.0"
  loop: dev-loop
---

# Skill: safe-change

## WHAT

### Purpose và context
- **Purpose:** sửa code dùng chung (hàm/class/module có nhiều caller) mà không làm gãy caller hiện có.
- **Trigger (when to use):** Modifying any function, class, or module called from more than one place.
- **Non-goals:** không refactor tiện tay code kề bên, không viết thêm test ngoài phạm vi task, không tự tìm caller bằng tay thay `impact-check`.

### Mental model
`symbol dùng chung → impact-check (callers + dependents) → hành vi quan sát được hiện tại → thay đổi tối thiểu → từng caller: tương thích ngược hoặc cập nhật tường minh → test (nếu có) → "Changed X. Verified Y" → cổng kiểm của repo`.

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | symbol/module cần sửa + yêu cầu thay đổi | có | thứ có hơn một caller |
| In | test của module | không | có thì chạy; không có thì ghi rõ trong commit message |
| Out | thay đổi tối thiểu + caller đã xác minh/cập nhật | có | mọi caller từ bước 1 đều được xét |
| Out | câu xác nhận "Changed X. Verified Y still works." | có | rồi chạy cổng kiểm của repo |

### Rules và capabilities
- RULE-01 (MUST): Backward compatibility impossible → surface to user before proceeding.
- RULE-02 (MUST): Touch only what task requires — no opportunistic refactoring.
- RULE-03 (MUST): No tests exist → acceptable to note — don't add tests outside task scope.
- Capabilities: truy vấn đồ thị caller/dependent; đọc + sửa code trong phạm vi task; chạy test cục bộ. Không ghi file ngoài phạm vi task.

### Failure boundaries
- Không giữ được tương thích ngược → **clarify**: dừng, báo user trước khi làm tiếp (RULE-01).
- Test đỏ sau khi sửa → **blocked**, không sang bước commit.
- Không có test → **partial** hợp lệ: ghi rõ trong commit message, không tự viết test.

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | deterministic | symbol | Chạy skill `impact-check` | danh sách callers + dependents | — |
| W02 | judgment | code hiện tại | Ghi lại hành vi quan sát được (return value, side effect) | baseline hành vi | — |
| W03 | effect | yêu cầu | Thay đổi tối thiểu, không đụng code kề bên | diff | không giữ được tương thích → B01 |
| W04 | judgment | callers W01 | Từng caller: xác minh tương thích ngược hoặc cập nhật tường minh | mọi caller đã xét | — |
| W05 | deterministic | test dir | Tìm test, có thì chạy | rc 0 hoặc ghi chú "no tests" | test đỏ → blocked; không test → B02 |
| W06 | effect | kết quả | Xác nhận + chạy cổng kiểm của repo (lệnh trong CLAUDE.md/AGENTS.md, vd `pnpm verify`) | câu xác nhận + kết quả cổng | — |

Chi tiết từng bước (nguồn chân lý cho W01–W06):

1. Run `impact-check` skill — get list of all callers and dependents.
2. Note current observable behaviour (return values, side effects).
3. Make minimal change. Don't touch adjacent code.
4. For each caller from step 1: verify backward-compatible or explicitly update caller.
5. `CHECK: ls <test-dir>/*<module>* 2>/dev/null | head -3` — if tests exist, `RUN: <test-cmd>`. If none, note explicitly in commit message.
6. Confirm: "Changed X. Verified Y still works." Then run the repo's own gate (the command named in CLAUDE.md/AGENTS.md, e.g. `pnpm verify`).

### Branches
| ID | Kind | Guard | Hành vi | Skip / failure | Rejoin |
|---|---|---|---|---|---|
| B01 | recovery | không thể giữ backward compatibility | dừng, báo user trước khi làm tiếp | user không duyệt → cancelled | W04 sau khi user duyệt |
| B02 | conditional_required | không có test cho module | ghi rõ "no tests" trong commit message, không viết test mới | — | W06 |

### Validation và stopping
Điều kiện đi tiếp: mọi caller trong danh sách `impact-check` đã được xét, và test (nếu có) rc 0. Dừng ở câu xác nhận + cổng kiểm của repo; không tự refactor thêm.

### Examples
- **Positive:** thêm tham số optional `timeout=30` vào `fetch_page()` có 4 caller → impact-check liệt kê 4 caller, cả 4 không truyền tham số nên tương thích → test module xanh → "Changed fetch_page signature. Verified 4 callers still work." → cổng kiểm của repo xanh.
- **Boundary/failure:** đổi kiểu trả về `get_user()` từ dict sang object, 2 caller dùng `user["id"]` → không giữ được tương thích → dừng, báo user (B01), chưa sửa caller khi chưa được duyệt.
