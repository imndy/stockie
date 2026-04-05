# Stockie — Project Knowledge Base
> Tài liệu này dành cho AI agent sessions tiếp theo. Đọc trước khi làm việc với dự án.
> Cập nhật lần cuối: 2026-04-05

---

## 1. Tổng quan dự án

**Mục tiêu:** Tự động thu thập, phân tích và lưu trữ dữ liệu chứng khoán Việt Nam cho một danh sách mã cổ phiếu, push kết quả lên GitHub mỗi ngày.

**Repo GitHub:** https://github.com/imndy/stockie (branch `main`)

**Đường dẫn local:** `C:\Users\dtran\OneDrive\Duy_Data\Trade\Stockie`

**Python environment:** `.venv\` (Python 3.12.10)

**Thư viện chính:** `vnstock` (nguồn dữ liệu VN), `pandas`, `xlsxwriter`

---

## 2. Cấu trúc thư mục

```
Stockie/
├── .gitignore               # loại trừ .venv/, *.xlsx, *.log, run_daily.log
├── run_daily.ps1            # PowerShell script chạy pipeline + ghi log
├── agent/
│   └── project_knowledge.md  # file này
├── draft/
│   ├── analyze.py           # script chính (toàn bộ logic)
│   ├── input/
│   │   └── stocks.csv       # danh sách ticker (cột 'ticker')
│   └── output/
│       ├── per_ticker/      # <TICKER>.md — 1 file/mã, update in-place
│       ├── daily/YYYYMMDD/  # summary.md + daily_*.xlsx
│       ├── quarterly/YYYYQx/# summary.md + quarterly_*.xlsx
│       ├── full/YYYYMMDD/   # summary.md + full_*.xlsx + full_*.txt
│       └── foreign_flow_history.csv  # tích lũy dòng tiền NN theo ngày
└── instructions/
    ├── huong_dan_phan_tich_ma_co_phieu.md
    └── vn_stock_trading_backbone.md
```

---

## 3. Danh sách mã theo dõi (stocks.csv)

13 mã HOSE: `HPG, MBB, ACB, SAB, VNM, VCB, FPT, MSN, VHM, MWG, TCB, SSI, VIC`

Thêm/bớt mã: sửa `draft/input/stocks.csv`. Nếu mã mới chưa có `.md` → pipeline tự chạy `full` mode cho mã đó.

---

## 4. Pipeline chính — analyze.py

### Cách chạy

```powershell
.venv\Scripts\python.exe draft\analyze.py --mode daily      # mỗi ngày
.venv\Scripts\python.exe draft\analyze.py --mode quarterly  # mỗi quý
.venv\Scripts\python.exe draft\analyze.py --mode full       # tất cả
```

### 3 modes

| Mode | Tần suất | Nội dung | Số req/mã |
|---|---|---|---|
| `daily` | Mỗi ngày | Giá, kỹ thuật, tin tức, dòng tiền NN, sự kiện | ~7 |
| `quarterly` | Mỗi quý | Tài chính, ban lãnh đạo, cổ đông lớn | ~9 |
| `full` | Lần đầu hoặc reset | Tất cả | ~16 |

### Nguồn dữ liệu

| Nguồn | Dữ liệu |
|---|---|
| **VCI** | price history, trading_stats, ratio_summary, price_board, intraday, **news (10 items)**, events |
| **KBS** | overview, shareholders, officers, subsidiaries, affiliate, income_statement, balance_sheet, cash_flow, ratio |

### Output per-ticker (`output/per_ticker/<TICKER>.md`)

File dùng sentinel để update in-place:
```
<!-- BEGIN:DAILY -->   ... <!-- END:DAILY -->
<!-- BEGIN:QUARTERLY --> ... <!-- END:QUARTERLY -->
```
- `daily` run → chỉ replace block DAILY
- `quarterly` run → chỉ replace block QUARTERLY

### Output summary (`output/daily/YYYYMMDD/summary.md`)

Gồm:
- Bảng so sánh tất cả mã (giá, P/E, P/B, ROE, EPS, tăng trưởng)
- Bảng giá đầy đủ (price_board)
- **Bảng so sánh nội ngành** (group theo `symbols_by_industries`)
- Link đến từng per-ticker file

---

## 5. Nội dung block DAILY trong per-ticker

Thứ tự các section:
1. Thống kê giao dịch (VCI trading_stats — 24 cột)
2. **Chỉ báo kỹ thuật: EMA20, EMA50, RSI(14), MACD** (tính từ lịch sử giá)
3. **Dòng tiền khối ngoại snapshot** (foreign_volume, foreign_room, holding_ratio)
4. **Dòng tiền khối ngoại lịch sử 10 phiên** (từ `foreign_flow_history.csv` tích lũy)
5. Tóm tắt chỉ số tài chính (ratio_summary — 46 cột)
6. **Tin tức Top 10** (VCI news — trả về 10 bản ghi)
7. **Lịch sự kiện 15 gần nhất** (VCI events — AIS/DIV/ISS, không có ĐHCĐ)
8. Lịch sử giá 20 phiên gần nhất
9. Giao dịch trong ngày 10 lệnh gần nhất

---

## 6. Rate Limiting

**API key:** Community tier — 60 req/phút (lưu persistent trong `vnai`)

```python
API_CALLS_PER_MIN = 57  # buffer 3 req
```

**Cơ chế:** Proactive rolling-window throttler (`_throttle()`) — đếm calls trong 62s window, tự chờ đúng lượng trước khi bị giới hạn. Thay thế hoàn toàn fixed delay giữa mỗi mã.

Để thay đổi tier:
```python
# Guest (chưa có key): 18
# Community (key miễn phí): 57   ← hiện tại
# Sponsor 180/min: 175
API_CALLS_PER_MIN = 57
```

---

## 7. Auto-push GitHub

Sau khi pipeline chạy xong, tự động:
```
git add -A → git pull --rebase --autostash → git commit → git push
```

Commit message format: `[auto] daily update 2026-04-05 07:30`

Fix non-fast-forward: `git pull --rebase --autostash` trước push — xử lý khi remote có commit mới hơn local.

---

## 8. Automation — Windows Task Scheduler

**Task name:** `Stockie Daily Pipeline`

| Setting | Giá trị |
|---|---|
| Schedule | Daily 07:30 |
| Script | `run_daily.ps1` |
| LogonType | `S4U` (chạy kể cả khi lock screen, không cần password) |
| WakeToRun | `True` |
| StartWhenAvailable | `True` (chạy bù nếu lỡ giờ) |
| DisallowStartIfOnBatteries | `False` |
| Log | `run_daily.log` (gitignored) |

**Wake from sleep:** Đã bật `Wake Timers` trong Windows Power Plan (AC + DC).
- Sleep → máy tự dậy lúc 7:30, chạy xong
- Hibernate / Tắt máy hoàn toàn → **không** wake được

**Kiểm tra task:**
```powershell
Get-ScheduledTaskInfo -TaskName "Stockie Daily Pipeline" | Select-Object LastRunTime, LastTaskResult, NextRunTime
```

---

## 9. Các giới hạn đã biết của vnstock

| Vấn đề | Lý do | Workaround |
|---|---|---|
| Events VCI chỉ có AIS/DIV/ISS | API không expose ĐHCĐ/chốt quyền | Hiển thị 15 sự kiện gần nhất giữ nguyên |
| Dòng tiền NN không có lịch sử theo phiên từ API | `quote.history` chỉ trả OHLCV | Tích lũy từng ngày vào `foreign_flow_history.csv` |
| VCI `events()` đôi khi trả rỗng | Rate limit hoặc server | `safe_call` retry 2 lần |
| KBS `events()` luôn trả rỗng | Source không hỗ trợ | Dùng VCI |
| Price board MultiIndex columns | VCI trả nested columns | `_flat_df()` flatten trước khi write Excel |

---

## 10. Các file quan trọng

| File | Mục đích |
|---|---|
| `draft/analyze.py` | Toàn bộ pipeline logic |
| `draft/input/stocks.csv` | Danh sách mã theo dõi |
| `draft/output/per_ticker/*.md` | Output chính — 1 file/mã |
| `draft/output/daily/YYYYMMDD/summary.md` | Tổng hợp daily |
| `draft/output/foreign_flow_history.csv` | Tích lũy dòng tiền NN |
| `run_daily.ps1` | Runner script cho Task Scheduler |
| `instructions/huong_dan_phan_tich_ma_co_phieu.md` | Hướng dẫn phân tích |
| `instructions/vn_stock_trading_backbone.md` | Framework giao dịch |

---

## 11. Lịch sử phát triển (commit log tóm tắt)

| Ngày | Nội dung |
|---|---|
| 2026-04-03 | Initial commit — pipeline cơ bản, 3 modes, per-ticker MD, Excel output |
| 2026-04-04 | Setup GitHub auto-push sau pipeline |
| 2026-04-04 | Thêm EMA20/EMA50/RSI(14), Top-10 news (VCI), events calendar, sector comparison |
| 2026-04-04 | Thêm MACD, fix events filter (bỏ cutoff), tích lũy foreign flow history CSV |
| 2026-04-04 | Proactive rate limiter (rolling window thay fixed delay) |
| 2026-04-04 | Tích hợp Community API key (60/min), bump `API_CALLS_PER_MIN=57` |
| 2026-04-05 | Fix Task Scheduler LogonType → S4U, bật WakeToRun + Wake Timers |
| 2026-04-05 | Fix git push non-fast-forward bằng `pull --rebase --autostash` |

---

## 12. Hướng phát triển tiếp theo (chưa làm)

- [ ] Thêm mã vào watchlist (sửa `stocks.csv`)
- [ ] Chạy `quarterly` mode theo lịch quý
- [ ] Tích hợp AI để tự động viết nhận xét phân tích vào per-ticker MD
- [ ] Dashboard web đọc dữ liệu từ GitHub repo
- [ ] Alert qua Telegram/email khi có tín hiệu kỹ thuật đặc biệt (RSI < 30, MACD cross)
