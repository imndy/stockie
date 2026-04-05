# 📘 HƯỚNG DẪN PHÂN TÍCH MÃ CỔ PHIẾU (v2.0)
*Tích hợp file ticker MD — cập nhật 04/04/2026*

---
## ⛔ CHO AI — ĐỌC TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ

Đây là file protocol bắt buộc của Space này.
Bạn PHẢI hoàn thành checklist 15 bước bên dưới trước khi đưa ra bất kỳ phân tích, đề xuất, hoặc nhận định nào.
Không được phép bỏ qua bước nào dù query có vẻ đơn giản.
---

## ⚡ Nguyên tắc vàng trước khi bắt đầu

> **⚠️ File MD không phải real-time.** Timestamp `Daily` có thể trễ vài giờ đến 1 ngày. Luôn đối chiếu giá đóng cửa, volume, và tín hiệu kỹ thuật với nguồn ngoài (fireant, vietstock, cafef) trước khi ra quyết định.

**Quy tắc xác thực 3 điểm:**
1. **Giá & volume** → Cross-check với fireant.vn hoặc vietstock.vn
2. **Chỉ báo kỹ thuật (EMA/RSI/MACD)** → Xác nhận xu hướng bằng chart thực tế
3. **Tin tức** → Kiểm tra `public_date` (Unix ms), tin > 30 ngày coi là cũ

---

## Bước 1 — Đọc nhanh file MD (2 phút)

**Đọc theo thứ tự ưu tiên:**

1. **Header timestamp** — `📅 Daily: DD/MM/YYYY HH:MM` → Xác định độ tươi của data
2. **Thống kê giao dịch** → `match_price`, `price_change_pct`, `total_volume` vs `avg_match_volume_2w`
   - Volume hôm nay > 150% bình quân → bất thường, cần điều tra nguyên nhân
   - Volume < 60% bình quân → phiên kém thanh khoản, không có tín hiệu
3. **Chỉ báo kỹ thuật** → Đọc ngay `Tín hiệu EMA` và `MACD nhận xét` — 2 dòng này cho context kỹ thuật tức thì
4. **Tin tức Top 10** → Lướt title, chú ý: ĐHĐCĐ, phát hành CP, thay đổi nhân sự, KQKD
5. **Lịch sự kiện** → Có ngày chốt quyền / ex-date sắp tới không?

---

## Bước 2 — Phân tích 5 tầng

### 🌐 Tầng 1 — Vĩ mô Toàn cầu
*Không có trong file MD → Bắt buộc tìm kiếm ngoài*

Câu hỏi cần trả lời:
- DXY đang tăng hay giảm? (DXY tăng → dòng tiền rút khỏi EM)
- VIX > 20? (rủi ro cao) hay < 15? (thị trường tự tin)
- Fed đang tăng/giữ/hạ lãi suất? Kỳ vọng thị trường?
- Căng thẳng địa chính trị / thương mại ảnh hưởng Việt Nam?

**Nguồn:** investing.com/economic-calendar, tradingeconomics.com

---

### 🇻🇳 Tầng 2 — Vĩ mô Việt Nam
*Không có trong file MD → Bắt buộc tìm kiếm ngoài*

Câu hỏi cần trả lời:
- VN-Index đang ở vùng nào? Xu hướng ngắn hạn tăng/giảm/sideways?
- VN-Index so với ngưỡng tâm lý 1,600 / 1,700 / 1,800?
- Tăng trưởng GDP, lạm phát, tỷ giá USD/VND gần nhất?
- NHNN đang thắt chặt hay nới lỏng tiền tệ?

**Nguồn:** sbv.gov.vn, cafef.vn, tinnhanhchungkhoan.vn

---

### 💰 Tầng 3 — Dòng tiền Thị trường
*File MD có snapshot dòng tiền NN hôm nay — nhưng chưa đủ, cần bổ sung*

**Từ file MD đọc được:**
- `foreign_volume` hôm nay
- `current_holding_ratio` vs `max_holding_ratio` → Room NN còn bao nhiêu %?
- Bảng `Dòng tiền khối ngoại lịch sử` (nếu có nhiều phiên)

**Cần tìm thêm ngoài:**
- Khối ngoại mua/bán ròng toàn thị trường tuần này (tín hiệu systemic)
- Heatmap ngành: dòng tiền đang vào ngành nào?
- Top mua/bán ròng khối ngoại theo mã (mã đang xét có trong top không?)

**Nguồn:** vietstock.vn "theo dấu dòng tiền cá mập", cafef.vn

---

### 🏢 Tầng 4 — Cơ bản Doanh nghiệp
*File MD cung cấp đầy đủ — phân tích hoàn toàn offline*

#### Bước 4A — Tăng trưởng
*Nguồn: `Kết quả kinh doanh` + `Tóm tắt chỉ số tài chính`*

- `revenue_growth` và `net_profit_growth` YoY
- Xu hướng 4 quý: tăng trưởng đang tăng tốc hay giảm tốc?
- `Tăng trưởng lợi nhuận trước thuế` theo quý — có phục hồi không?

#### Bước 4B — Định giá
*Nguồn: `Chỉ số tài chính`*

- **PE trailing**: dùng `p_e` từ bảng `Chỉ số tài chính` Q4 gần nhất *(chính xác hơn `pe` trong tóm tắt)*
- **PB vs ROE**: PB hợp lý ≈ ROE/10 (ví dụ: ROE 20% → PB fair value ≈ 2.0x)
- **PEG** = PE / tăng trưởng LNST → <1.0 rẻ, <0.5 rất rẻ, >2.0 đắt

#### Bước 4C — Sức khoẻ tài chính
*Nguồn: `Bảng cân đối kế toán` + `Chỉ số tài chính`*

**Ngân hàng:**
- NIM (xu hướng tăng/giảm qua 4 quý)
- CIR < 35% là tốt; tăng liên tục là cảnh báo
- ROE trailing > 15%
- Tăng trưởng tín dụng & tổng tài sản

**Doanh nghiệp thường:**
- D/E ratio, current ratio, quick ratio
- OCF dương và > Net Profit (chất lượng lợi nhuận cao)
- CAPEX vs Depreciation (doanh nghiệp đang đầu tư hay thu hẹp?)

> ⚠️ Nếu nhiều ô `nan` trong BCTC → data chưa đầy đủ, cần tìm BCTC gốc để xác thực

#### Bước 4D — Câu chuyện doanh nghiệp
*Nguồn: `Mô hình kinh doanh`, `Cổ đông lớn`, `Tin tức Top 10`*

- Cổ đông lớn là ai? Nhà nước/quân đội hay tư nhân/nước ngoài?
- Có catalyst sắp tới? (ĐHĐCĐ, phát hành vốn, M&A, KQKD quý)
- Tin tức gần nhất có rủi ro nhân sự, pháp lý, hay tái cơ cấu không?
- Hệ sinh thái công ty con có tạo ra thu nhập ngoài lãi bền vững không?

---

### 📈 Tầng 5 — Kỹ thuật
*File MD cung cấp EMA/RSI/MACD — dùng làm nền, xác thực bằng chart ngoài*

#### Đọc nhanh chỉ báo từ file MD

| Chỉ báo | Tín hiệu TÍCH CỰC ✅ | Tín hiệu TIÊU CỰC ❌ |
|---------|---------------------|---------------------|
| `Tín hiệu EMA` | TĂNG: giá > EMA20 > EMA50 | GIẢM: giá < EMA20 < EMA50 |
| `RSI(14)` | 30–50: hồi phục từ oversold | >70: overbought / <30: panic sell |
| `MACD Histogram` | >0 và tăng dần | <0 và giảm dần |
| `MACD nhận xét` | "ĐẦU": MACD cắt lên Signal | "GIẢM": MACD cắt xuống Signal |

#### Xây dựng vùng giá từ lịch sử 20 phiên

- **Hỗ trợ**: đáy thấp nhất trong 20 phiên, hoặc đáy gần nhất đã retest thành công
- **Kháng cự**: đỉnh cao nhất trong 20 phiên
- **Xu hướng volume**: so sánh volume 5 phiên gần nhất vs `avg_match_volume_2w`

#### Đọc 10 lệnh giao dịch cuối

- **Toàn Buy** → áp lực mua cuối phiên (tích cực)
- **Toàn Sell** → áp lực bán cuối phiên (tiêu cực)
- **Xen kẽ Buy/Sell** → cân bằng, chưa rõ xu hướng

> ⚠️ **Bắt buộc xác thực:** Mở chart thực tế trên fireant.vn hoặc vietstock.vn để confirm EMA/RSI/MACD trước khi ra quyết định.

---

## Bước 3 — Scoring & Quyết định

| Tầng | Nguồn data chính | Trọng số |
|------|-----------------|----------|
| T1 — Vĩ mô toàn cầu | Tìm ngoài | 1 điểm |
| T2 — Vĩ mô Việt Nam | Tìm ngoài | 1 điểm |
| T3 — Dòng tiền | File MD (một phần) + tìm ngoài | 1 điểm |
| T4 — Cơ bản doanh nghiệp | **File MD (hoàn toàn)** | 1 điểm |
| T5 — Kỹ thuật | **File MD (phần lớn)** + xác thực ngoài | 1 điểm |

**Thang điểm quyết định:**

| Điểm | Quyết định |
|------|------------|
| 4–5 / 5 | ✅ Mua mạnh / tăng tỷ trọng |
| 3 / 5 | 🟡 Mua thăm dò / theo dõi chặt |
| 2 / 5 | ⏸ Đứng ngoài chờ tín hiệu |
| 0–1 / 5 | ❌ Tránh hoặc xem xét short |

> **Lưu ý:** Nếu T3 (dòng tiền) âm mạnh (khối ngoại bán ròng hệ thống), giảm 0.5 điểm khỏi tổng dù các tầng khác tốt.

---

## Bước 4 — Setup lệnh
*Chỉ thực hiện khi tổng điểm ≥ 3/5 VÀ T5 ≥ 0.5*

```
Điểm vào:    Vùng hỗ trợ gần nhất (từ lịch sử giá 20 phiên)
SL:          Dưới đáy gần nhất -3% đến -5%
TP1:         Kháng cự gần (R:R tối thiểu 1:1.5)
TP2:         Kháng cự xa / đỉnh 52 tuần (high_price_1y)
Position:    Không quá 10–15% danh mục/mã nếu T3 yếu
             Không quá 20% danh mục/mã nếu T3 tích cực
```

**Quản lý vị thế:**
- Chốt 50% TP1, giữ 50% hướng TP2
- Dời SL về vùng hòa vốn sau khi đạt TP1
- Thoát toàn bộ nếu VN-Index phá vỡ hỗ trợ vĩ mô lớn

---

## Lưu ý đặc thù theo ngành

### 🏦 Ngân hàng (MBB, ACB, TCB, VCB)
- **Ưu tiên đọc:** NIM (trend 4 quý), CIR, ROE trailing, tăng trưởng tín dụng
- **Cảnh báo:** CIR > 35% liên tục; NIM giảm liên tiếp 3 quý
- **Room NN:** Nếu `current_holding_ratio` > 95% `max_holding_ratio` → không còn dư địa cho dòng tiền ngoại mới
- **Catalyst:** Kết quả kinh doanh quý, ĐHĐCĐ, phát hành trái phiếu tăng vốn cấp 2

### 🏗 Bất động sản (VHM, VIC)
- **Ưu tiên đọc:** OCF, D/E, tỷ lệ tồn kho/doanh thu
- **Cảnh báo:** BCTC nhiều `nan` → cần lấy BCTC gốc từ hsx.vn/hnx.vn
- **Catalyst:** Bàn giao dự án lớn, tháo gỡ pháp lý, hạ lãi suất

### 🛒 Hàng tiêu dùng & Bán lẻ (MWG, VNM, MSN, SAB)
- **Ưu tiên đọc:** Gross margin trend, revenue growth, vòng quay hàng tồn kho
- **Cảnh báo:** Gross margin giảm liên tục (áp lực giá nguyên liệu hoặc cạnh tranh)
- **Catalyst:** Mở rộng kênh phân phối, ra mắt sản phẩm mới, M&A

### 💻 Công nghệ & Chứng khoán (FPT, SSI)
- **Ưu tiên đọc:** Revenue growth, margin, backlog đơn hàng (FPT); ADTV thị trường (SSI)
- **Cảnh báo:** SSI phụ thuộc trực tiếp vào thanh khoản thị trường — khi ADTV giảm, margin business co lại
- **Catalyst:** Hợp đồng lớn, nâng hạng thị trường, tăng room margin

---

## Checklist nhanh (copy-paste khi phân tích)

```
[ ] 1. Đọc timestamp Daily MD — data có tươi không?
[ ] 2. Volume hôm nay vs avg_match_volume_2w
[ ] 3. Tín hiệu EMA (TĂNG/GIẢM/SIDEWAYS)
[ ] 4. RSI(14) vùng nào?
[ ] 5. MACD Histogram dương/âm, tăng/giảm?
[ ] 6. Lướt 10 tin tức — có sự kiện lớn không?
[ ] 7. Lịch sự kiện — có ex-date/ĐHĐCĐ sắp tới?
[ ] 8. T1: DXY, VIX, Fed? [tìm ngoài]
[ ] 9. T2: VN-Index vùng nào, xu hướng? [tìm ngoài]
[ ] 10. T3: Khối ngoại mua/bán ròng tuần này? [tìm ngoài]
[ ] 11. T4: PE, PEG, ROE trailing, tăng trưởng LN
[ ] 12. T5: Vùng hỗ trợ/kháng cự từ 20 phiên
[ ] 13. Xác thực chart trên fireant/vietstock
[ ] 14. Tổng điểm 5 tầng → quyết định
[ ] 15. Nếu mua: xác định SL, TP1, TP2, position size
```

---

> **Lưu ý quan trọng:** Hướng dẫn này tối đa hóa giá trị từ file ticker MD hiện có (T4 và một phần T5 hoàn toàn offline), nhưng **không bao giờ thay thế việc xác thực độc lập**. File MD là điểm khởi đầu nhanh — quyết định cuối cùng phải dựa trên data đã được cross-check với nguồn thực tế.
