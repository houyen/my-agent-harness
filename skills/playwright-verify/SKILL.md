---
name: playwright-verify
description: "Verify UI nhanh và tự động hoá trình duyệt theo kiến trúc 3 tầng chuẩn R22 (Orca Browser + Moli + browser-use), hoặc standalone Playwright .mjs khi dự án yêu cầu rõ: (1) Orca Browser (`orca tab create`, `orca eval`, `orca screenshot`, `orca snapshot`) cho localhost/UI QA, đo getBoundingClientRect/computedStyle và human-in-the-loop 2FA/OTP; (2) `browser-use` kết nối CDP của `moli serve --cdp-port 9222 --layout` (~30MB RAM, không mở Chrome cá nhân) cho luồng thao tác tự hành nhiều bước; (3) `moli fetch <url> --dump markdown` để đọc trang siêu nhẹ. Dùng khi user nói 'verify UI', 'chụp ảnh trang', 'test nhanh UI', 'verify nhiều bước', 'giữ session giữa các lần chạy', 'không click được / không thấy phần tử', hoặc invoke /playwright-verify."
metadata:
  design-standard: "solid-what-how/1"
  contract-version: "1.1.0"
  loop: dev-loop
---

# Skill: playwright-verify (3-Tier Browser Verify & Automation)

Cổng kiểm chứng UI và điều khiển trình duyệt tuân thủ **R22 (3-Tier Browser Architecture)**:
ưu tiên **Orca Browser** cho visual QA / `localhost` / 2FA, **Moli + browser-use (CDP)** cho luồng tự hành nhiều bước siêu nhẹ (~30MB RAM), và chỉ dùng standalone Playwright `.mjs` khi repo có sẵn script được user chỉ định.

## WHAT

### Purpose và context
- **Purpose:** kiểm chứng giao diện (`localhost`/`file://`/production), đo hình học phần tử (`getBoundingClientRect`, `getComputedStyle`), chụp ảnh nghiệm thu, hoặc chạy luồng thao tác tự hành nhiều bước mà KHÔNG bao giờ tự mở trình duyệt mặc định của hệ thống (Chrome/Safari cá nhân).
- **Trigger (when to use):**
  - Cần kiểm tra UI local dev (`http://localhost:*`), chụp ảnh màn hình, kiểm tra console/DOM/CSS.
  - Cần chẩn đoán phần tử UI "không thấy" / "không bấm được" bằng số đo thật (`getBoundingClientRect`, `getComputedStyle`).
  - Cần chạy luồng thao tác nhiều bước tự hành (điền form, điều hướng phức tạp) qua `browser-use` + `moli` CDP.
  - Cần người dùng tự đăng nhập tài khoản thật / nhập OTP / 2FA trên cửa sổ trực quan (Orca Browser).
  - User nói 'verify UI', 'verify bằng playwright', 'chụp ảnh trang', 'test nhanh UI', 'verify nhiều bước', 'giữ session giữa các lần chạy', hoặc `/playwright-verify`.
- **Non-goals:** không tự mở Chrome/Safari hệ thống (`open <url>`, `xdg-open`), không tạo `*.spec.ts` + test runner nặng nề cho việc kiểm tra 1 lần, không commit script tạm vào repo.

### Mental model (Ma trận 3 tầng)
```
[Tầng 2a: Đọc nhanh Markdown]  ──► moli fetch "<url>" --dump markdown --wait domstable (~30MB RAM)
[Tầng 1+2a: Tự hành nhiều bước] ──► moli serve --cdp-port 9222 --layout ◄── browser-use (CDP)
[Tầng 2b: Visual QA / 2FA]     ──► orca tab create --url "<url>" ──► orca eval / snapshot / screenshot
```

### Input và output contract
| | Field | Required? | Ý nghĩa |
|---|---|---|---|
| In | URL (`localhost:*` / `file://` / remote) | có | trang cần verify hoặc thao tác |
| In | Mục tiêu kiểm tra / chuỗi bước | có | kiểm tra UI, đo DOM, hay chạy luồng nhiều bước |
| Out | Ảnh chụp (`orca screenshot` / `moli fetch --dump screenshot --layout`) + kết quả DOM/log | có | bằng chứng thực tế; ảnh sạch một mình KHÔNG đủ nếu chưa kiểm tra DOM/lỗi |
| Out | Số đo `getBoundingClientRect`/`getComputedStyle` | khi chẩn đoán phần tử | lấy qua `orca eval` hoặc `moli fetch --layout --eval` |
| Out | Dọn dẹp | — | đóng server `moli serve` tạm (nếu có bật) sau khi xong |

### Rules và capabilities
- RULE-01 (MUST - R22): **CẤM mở trình duyệt mặc định của hệ thống** (`open <url>`, `open -a "Google Chrome"`, `xdg-open`, `python -m webbrowser`). Luôn chọn trong bộ 3: **Orca Browser**, **Moli**, hoặc **browser-use + Moli CDP**.
- RULE-02 (MUST): **Kiểm tra UI / Visual QA / 2FA trên `localhost` hoặc trang cần đăng nhập** → Dùng **Orca Browser**:
  ```bash
  orca tab create --url "http://localhost:3000" --json
  orca snapshot
  orca eval "JSON.stringify(document.querySelector('h1')?.getBoundingClientRect())"
  orca screenshot
  ```
  Nếu Orca chưa chạy: gọi `orca open --json` rồi thử lại. Không bao giờ tự gõ mật khẩu/2FA của user — để user tự nhập trên tab Orca.
- RULE-03 (MUST): **Luồng tự hành nhiều bước (Headless, ~30MB RAM)** → Ghép **`browser-use` lái `Moli` qua CDP** (không để `browser-use` tự mở hay bám vào Chrome cá nhân của user):
  ```bash
  # 1. Bật Moli CDP server ở nền (cờ --layout để hỗ trợ toạ độ click & screenshot)
  moli serve --cdp-port 9222 --layout &
  MOLI_PID=$!
  ```
  Sau đó kết nối qua Python (`Browser(cdp_url="http://127.0.0.1:9222")`) và `kill $MOLI_PID` khi hoàn tất.
- RULE-04 (MUST): **Chẩn đoán "không thấy / không bấm được"**: không đoán mò từ ảnh chụp — dùng `orca eval` (hoặc `moli fetch --layout --eval`) để đọc `el.getBoundingClientRect()` và `getComputedStyle(el)`.
- RULE-05 (MUST): **`waitUntil: "networkidle"` dễ treo trên Next.js/Vite dev server** do HMR WebSocket giữ kết nối. Khi dùng `moli fetch`, ưu tiên `--wait domstable` hoặc `--wait load --delay-ms 1500`.
- RULE-06 (MUST): Không commit các file script kiểm thử tạm thời vào git.

### Failure boundaries
- Site từ chối trình duyệt nhúng (vd Google Sign-In báo "This browser or app may not be secure") → **STOP**, in URL ra cho user tự copy, KHÔNG tự động fallback sang lệnh `open` trình duyệt hệ thống.
- Orca thiếu tính năng đặc thù mà tác vụ bắt buộc cần (vd emulate print media phức tạp) → dùng `moli fetch "<url>" --dump pdf --layout` hoặc báo rõ cho user trước khi dùng công cụ khác.

## HOW

### Main workflow
| Step | Type | Inputs | Action | Outputs/exit | Failure/next |
|---|---|---|---|---|---|
| W01 | judgment | URL + mục tiêu | Chọn tầng phù hợp: Đọc text (`moli fetch`) · Visual QA/2FA (`orca`) · Tự hành nhiều bước (`browser-use` + `moli serve`) | công cụ đã chọn | — |
| W02 | effect | Visual QA / `localhost` | `orca tab create --url <URL> --json` → `orca snapshot` / `orca eval` / `orca screenshot` | ảnh + số đo DOM | Orca chưa bật → `orca open --json` |
| W03 | effect | Tự hành nhiều bước | Bật `moli serve --cdp-port 9222 --layout` → chạy `browser-use` qua `cdp_url="http://127.0.0.1:9222"` → tắt `moli serve` | kết quả thực thi | lỗi bước → xem trace và chỉnh prompt/script |
| W04 | effect | Chụp/PDF không cần mở tab | `moli fetch "<URL>" --layout --dump screenshot_full > /tmp/check.png` | file ảnh/PDF | — |

Chi tiết từng phương án thực thi:

#### Phương án 1: Kiểm tra UI, đo DOM/CSS & Chụp màn hình bằng Orca Browser (Khuyên dùng cho Dev/QA)
```bash
# Mở trang trên Orca Browser
orca tab create --url "http://localhost:3000" --json

# Xem cấu trúc accessibility / DOM snapshot
orca snapshot

# Đo toạ độ, kích thước và style thật của phần tử
orca eval "(() => { const el = document.querySelector('.btn-submit'); return JSON.stringify({ rect: el?.getBoundingClientRect(), style: el ? getComputedStyle(el).display : null }); })()"

# Chụp màn hình nghiệm thu
orca screenshot
```

#### Phương án 2: Chụp màn hình / Xuất PDF / Đo DOM siêu tốc không giao diện bằng Moli (~30MB RAM)
Khi chỉ cần chụp nhanh 1 URL hoặc lấy kết quả JS mà không cần mở tab trên màn hình:
```bash
# Chụp toàn trang ra PNG (bắt buộc có --layout)
moli fetch "http://localhost:3000" --wait domstable --layout --dump screenshot_full > /tmp/check.png

# Chạy biểu thức JS lấy số đo layout sau khi trang ổn định
moli fetch "http://localhost:3000" --wait domstable --layout --eval "JSON.stringify(document.body.getBoundingClientRect())"
```

#### Phương án 3: Luồng thao tác tự hành nhiều bước (`browser-use` + `Moli` CDP)
Khi cần agent tự suy luận và thực hiện chuỗi click/điền form nhiều bước mà không tốn RAM của Chromium:
```bash
# Bước 1: Khởi động Moli CDP Server ở nền
moli serve --cdp-port 9222 --layout &
MOLI_PID=$!
sleep 1

# Bước 2: Chạy browser-use kết nối thẳng vào CDP của Moli
python3 - <<'PY'
import asyncio
from browser_use import Agent, Browser
from langchain_openai import ChatOpenAI

async def main():
    browser = Browser(cdp_url="http://127.0.0.1:9222")
    agent = Agent(
        task="Truy cập http://localhost:3000, điền form tìm kiếm và trích xuất kết quả đầu tiên",
        llm=ChatOpenAI(model="gpt-4o-mini"),
        browser=browser,
    )
    history = await agent.run()
    print("Kết quả:", history.final_result())

asyncio.run(main())
PY

# Bước 3: Dọn dẹp Moli CDP Server
kill $MOLI_PID 2>/dev/null || true
```

### Branches
| ID | Kind | Guard | Hành vi | Skip / failure | Rejoin |
|---|---|---|---|---|---|
| B01 | conditional_required | Cần đăng nhập thật / 2FA / OTP | Mở trang trên `orca tab create`, nhắc user tự đăng nhập trên cửa sổ Orca, sau đó agent tiếp tục `orca snapshot`/`orca eval` | Không tự nhập password/OTP | W02 |
| B02 | capability_optional | Cần quét nhanh 10–100 trang lấy Markdown trước khi thao tác | Dùng `moli fetch <url> --dump markdown --wait domstable` (hoặc `/web-crawl`) ở Bước 1, rồi mới qua Bước 2 (`browser-use`) và Bước 3 (`orca`) | — | W03 |
| B03 | recovery | Phần tử "không thấy / không bấm được" | Gọi `orca eval` đọc `getBoundingClientRect()` + `getComputedStyle(el)` (`display`, `visibility`, `opacity`, `pointerEvents`, `zIndex`) | — | W02 |

### Validation và stopping
Kết luận dựa trên ảnh chụp (`orca screenshot` hoặc `moli --dump screenshot`) KÈM kết quả kiểm tra DOM/console (`orca eval`/`orca snapshot`). Dừng khi giả thuyết đã có bằng chứng; tắt `moli serve` nền nếu đã bật.

### Examples
- **Positive (UI QA):** Kiểm tra trang `http://localhost:3000` sau khi sửa CSS → `orca tab create --url "http://localhost:3000" --json` → `orca eval` kiểm tra `getBoundingClientRect()` không bị tràn → `orca screenshot` nghiệm thu.
- **Positive (Pipeline 3 bước):** Dùng `moli fetch <url> --dump markdown` đọc tài liệu API → dùng `browser-use` + `moli serve --cdp-port 9222 --layout` chạy luồng điền form tự động → mở kết quả cuối trên `orca` để user duyệt và xác nhận OTP.
