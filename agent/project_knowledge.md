# Stockie — Project Knowledge Base
> Tài liệu này dành cho AI agent sessions tiếp theo. Đọc trước khi làm việc với dự án.
> Cập nhật lần cuối: 2026-04-05 (session 2)

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
│       │   └── bluechip_snapshot.md  # ← MỚI: tổng hợp tất cả ticker
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

**100 mã HOSE:**
`AAA, ACB, ANV, BCG, BCM, BID, BMP, BSI, BSR, BVH, BWE, CII, CMG, CTD, CTG, CTR, CTS, DBC, DCM, DGC, DGW, DIG, DPM, DSE, DXG, DXS, EIB, EVF, FPT, FRT, FTS, GAS, GEX, GMD, GVR, HAG, HCM, HDB, HDC, HDG, HHV, HPG, HSG, HT1, IMP, KBC, KDC, KDH, LPB, MBB, MSB, MSN, MWG, NAB, NKG, NLG, NT2, OCB, PAN, PC1, PDR, PHR, PLX, PNJ, POW, PPC, PTB, PVD, PVT, REE, SAB, SBT, SCS, SHB, SIP, SJS, SSB, SSI, STB, SZC, TCB, TCH, TLG, TPB, VCB, VCG, VCI, VGC, VHC, VHM, VIB, VIC, VIX, VJC, VND, VNM, VPB, VPI, VRE, VTP`

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
API_CALLS_PER_MIN = 25  # Community 60/min server-side
```

**Cơ chế:** Proactive rolling-window throttler (`_throttle()`) — đếm calls trong 60s window, tự chờ đúng lượng trước khi bị giới hạn. Thay thế hoàn toàn fixed delay giữa mỗi mã.

**Lý do đặt 25 thay vì 57:** vnstock dùng `tenacity` nội bộ để retry mỗi failed call 2-3 lần. Mỗi retry = 1 HTTP request thực. Trên non-trading days (cuối tuần), hầu hết calls fail → mỗi tracked call tiêu thụ 2-3 server requests. Vì vậy 25 tracked/min ≈ 50-75 server requests/min — an toàn dưới giới hạn 60.

Để thay đổi tier:
```python
# Guest (chưa có key): 10
# Community (key miễn phí): 25   ← hiện tại
# Sponsor 180/min: 75
API_CALLS_PER_MIN = 25
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
| Schedule | **T3–T7** (Tue–Sat) **07:20** — pipeline chạy T+1, capture data T2–T6 |
| Script | `run_daily.ps1` |
| LogonType | `S4U` (chạy kể cả khi lock screen, không cần password) |
| WakeToRun | `True` |
| StartWhenAvailable | `True` (chạy bù nếu lỡ giờ) |
| DisallowStartIfOnBatteries | `False` |
| Log | `run_daily.log` (gitignored) |

**Wake from sleep:** Đã bật `Wake Timers` trong Windows Power Plan (AC + DC).
- Sleep → máy tự dậy lúc 7:19, chạy piline từ 7:20, chạy xong
- Hibernate / Tắt máy hoàn toàn → **không** wake được

**Kiểm tra task:**
```powershell
Get-ScheduledTaskInfo -TaskName "Stockie Daily Pipeline" | Select-Object LastRunTime, LastTaskResult, NextRunTime
```

---

## 9. Các giới hạn đã biết của vnstock

| Vấn đề | Lý do | Workaround |
|---|---|---|
| Events VCI chỉ có AIS/DIV/ISS | API không expose ĐHCĐ/chốt quyền | Hiển thị sự kiện 90 ngày qua + 30 ngày tới |
| VCI `events()` có placeholder `1753-01-01` | Giá trị null của VCI | Skip nếu `year < 2000` |
| Dòng tiền NN không có lịch sử theo phiên từ API | `quote.history` chỉ trả OHLCV | Tích lũy từng ngày vào `foreign_flow_history.csv` |
| `foreign_volume` ≠ mua/bán ròng thực | VCI chỉ trả KL khớp NN (net), không có buy/sell riêng | Hiển thị N/A ở tổng hợp; cột NN trong bảng scan chỉ dùng so sánh tương đối |
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
| `draft/output/per_ticker/bluechip_snapshot.md` | **MỚI** — Tổng hợp tất cả ticker: kỹ thuật, định giá, sự kiện |
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
| 2026-04-05 | **Thêm `bluechip_snapshot.md`** — tổng hợp tất cả ticker (5 sections) |
| 2026-04-05 | Fix events bug `1753-01-01`, mở rộng window 90 ngày qua + 30 ngày tới |
| 2026-04-05 | Fix git stale rebase-merge directory (tự xóa trước khi pull --rebase) |
| 2026-04-05 | Đổi schedule Task Scheduler từ 07:30 → **07:20** |
| 2026-04-05 | N/A cho khối ngoại tổng hợp (foreign_volume ≠ mua/bán ròng thực) |

---

## 12. bluechip_snapshot.md — cấu trúc và nguồn dữ liệu

File tại `draft/output/per_ticker/bluechip_snapshot.md`, tự động generate sau mỗi daily run.

| Section | Nội dung | Nguồn |
|---|---|---|
| 1. Tổng quan dòng tiền | VN-Index, khối ngoại, nhóm mua/bán nhiều nhất | VCI VNINDEX history + tự tính |
| 2. Bảng scan kỹ thuật | Giá, %D, EMA20/50, RSI14, MACD Hist, NN KL, Tín hiệu | trading_stats + compute_technicals |
| 3. Bảng định giá nhanh | P/E, P/B, ROE, LNST growth, Room NN | ratio_summary VCI |
| 4. Sự kiện đáng chú ý | 90 ngày qua + 30 ngày tới, skip `1753-01-01` | events VCI |
| 5. Phân loại theo pha | Phòng thủ / Tăng trưởng / Chu kỳ + tín hiệu hôm nay | hardcoded sets + signal compute |

**Signal logic (`_compute_signal`):**
```
✅ TĂNG      = giá > EMA20 > EMA50 AND MACD hist ≥ 0
🔴 RỦI RO CAO = (giá dưới EMA20 hoặc EMA50) AND NN KL×giá > 50 tỷ
⚠️ GIẢM      = giá dưới EMA20 hoặc EMA50
🔄 TRUNG TÍNH = còn lại
```

**Lưu ý quan trọng:** Cột "NN hôm nay (tỷ)" = `foreign_volume × close / 1e9` — đây là KL khớp NN **không phải mua/bán ròng thực**. Dùng để so sánh tương đối giữa các mã, không dùng để kết luận mua/bán ròng.

**Sector sets (hardcoded, cập nhật khi thay đổi danh sách):**
```python
_SECTOR_DEFENSIVE = {"GAS", "VNM", "SAB", "PLX", "MSN"}
_SECTOR_GROWTH    = {"FPT", "MWG", "TCB", "VPB", "ACB", "MBB", "HDB", "LPB", "STB"}
_SECTOR_CYCLICAL  = {"HPG", "VHM", "VIC", "VRE", "CTG", "BID"}
```

---

## 13. Hướng phát triển tiếp theo (chưa làm)

- [ ] Chạy `quarterly` mode theo lịch quý (Task Scheduler riêng)
- [ ] Tích hợp AI để tự động viết nhận xét phân tích vào per-ticker MD
- [ ] Dashboard web đọc dữ liệu từ GitHub repo
- [ ] Alert qua Telegram/email khi có tín hiệu kỹ thuật đặc biệt (RSI < 30, MACD cross)
- [ ] Dòng tiền NN thực (buy/sell riêng) — cần nguồn khác (FireAnt, HOSE API)
