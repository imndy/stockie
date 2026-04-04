# 📋 Hướng Dẫn Phân Tích Hoàn Chỉnh Một Mã Cổ Phiếu
## Quy Trình Chuẩn — Từ Lọc Đến Ra Lệnh

> Tài liệu này được xây dựng từ backbone trading và phân tích thực chiến các mã HPG, MBB, ACB, MSN, VHM, SAB, VIC trong phiên 02/04/2026. Áp dụng cho swing trading vốn nhỏ trên thị trường chứng khoán Việt Nam.

---

## TỔNG QUAN: MÔ HÌNH 5 TẦNG PHÂN TÍCH

Một quyết định vào lệnh tốt phải đi từ **trên xuống dưới**, không bắt đầu từ chart.

```
TẦNG 1 ── Vĩ Mô Toàn Cầu        → Fed, DXY, dầu, vàng, địa chính trị
TẦNG 2 ── Vĩ Mô Việt Nam         → GDP, lãi suất, tỷ giá, nâng hạng FTSE
TẦNG 3 ── Dòng Tiền Thị Trường   → Khối ngoại, tự doanh, dòng tiền ngành
TẦNG 4 ── Cơ Bản Doanh Nghiệp    → Tài chính, định giá, sức khỏe nợ
TẦNG 5 ── Kỹ Thuật & Timing      → Chart, chỉ báo, entry/exit
```

> **Quy tắc:** Chỉ vào lệnh khi **tối thiểu 4/5 tầng ủng hộ.** Kỹ thuật đẹp nhưng vĩ mô xấu → không vào.

---

## BƯỚC 1: KIỂM TRA VĨ MÔ TOÀN CẦU

**Thời gian:** 5–10 phút mỗi buổi sáng  
**Công cụ:** TradingView, Investing.com/economic-calendar

### 1.1 Các biến số cần theo dõi hàng ngày

| Biến số | Tác động đến TTCK Việt Nam | Cảnh báo |
|---------|---------------------------|----------|
| **DXY (Chỉ số USD)** | DXY tăng → Dòng vốn rút khỏi EM → Khối ngoại bán | DXY > 105: thận trọng |
| **US 10Y Yield** | Lợi suất tăng → Cổ phiếu kém hấp dẫn, EM bị rút vốn | >4.5%: áp lực lớn |
| **VIX (Fear Index)** | VIX tăng → Rủi ro toàn cầu tăng → Dòng tiền về safe haven | VIX > 25: giảm vị thế |
| **Giá dầu (WTI/Brent)** | Ảnh hưởng CPI, ngành năng lượng, logistics | Dầu > 100 USD: rủi ro lạm phát |
| **Giá vàng** | Vàng tăng mạnh = Rủi ro cao, dòng tiền phòng thủ | Vàng tăng >2% trong ngày: cảnh báo |

### 1.2 Lịch sự kiện kinh tế quan trọng (Investing.com)

Trước khi vào lệnh, kiểm tra trong 3–5 ngày tới có:
- [ ] Họp FOMC / Phát biểu Fed không?
- [ ] CPI Mỹ / NFP (Non-Farm Payroll) không?
- [ ] Số liệu GDP Trung Quốc / châu Á không?

> **Quy tắc:** Nếu có sự kiện rủi ro lớn trong vòng 48h → Giảm size lệnh 50% hoặc đứng ngoài.

---

## BƯỚC 2: KIỂM TRA VĨ MÔ VIỆT NAM

**Thời gian:** 5 phút / 1–2 lần mỗi tuần  
**Công cụ:** sbv.gov.vn, SSI Research, BVSC Research, 24hmoney.vn

### 2.1 Checklist vĩ mô Việt Nam

| Yếu tố | Tích cực | Tiêu cực |
|--------|---------|---------|
| **GDP tăng trưởng** | >6.5% → Môi trường kinh doanh tốt | <5% → Doanh nghiệp khó khăn |
| **Lãi suất NHNN** | Giữ nguyên hoặc giảm → NIM ngân hàng OK | Tăng → Áp lực chi phí vốn |
| **Tỷ giá USD/VND** | Ổn định biến động <2%/năm | Biến động >4% → Áp lực nhập khẩu, lạm phát |
| **Tín dụng tăng trưởng** | >14% → Dòng tiền dồi dào | <10% → Kinh tế chậm |
| **Đầu tư công giải ngân** | Cao → Lợi cho thép, vật liệu, hạ tầng | Thấp → Ngành hưởng lợi không tăng được |
| **Nâng hạng FTSE EM** | Xác nhận → Dòng vốn ETF +500tr USD | Bị hoãn → Tâm lý thất vọng |

### 2.2 Nguồn đọc nhanh
- **Tháng 1, 4, 7, 10:** Báo cáo chiến lược quý từ SSI Research / BVSC
- **Hàng ngày:** 24hmoney.vn, Tinnhanhchungkhoan.vn, CafeF.vn (phần vĩ mô)
- **Chính sách tiền tệ:** sbv.gov.vn

---

## BƯỚC 3: PHÂN TÍCH DÒNG TIỀN THỊ TRƯỜNG

**Thời gian:** 10 phút trước khi thị trường mở  
**Công cụ:** FireAnt, Vietstock (tab khối ngoại), 24hmoney.vn

### 3.1 Phân tích khối ngoại

Khối ngoại là **chỉ báo thông minh** vì họ có thông tin tốt, phân tích bài bản hơn cá nhân nhỏ lẻ.

| Tín hiệu | Ý nghĩa | Hành động |
|---------|---------|----------|
| Mua ròng liên tiếp 3–5 phiên | Lạc quan trung hạn | Ưu tiên mua cùng chiều |
| Bán ròng >500 tỷ/phiên | Rủi ro ngắn hạn | Giảm size hoặc chờ |
| Bán ròng liên tiếp >10 phiên | Xu hướng rút vốn cấu trúc | Hạn chế vị thế, tăng tiền mặt |
| Đột ngột mua ròng sau chuỗi bán | Tín hiệu đảo chiều | Chú ý theo dõi, có thể vào thăm dò |

**Cách kiểm tra nhanh:**
1. Mở FireAnt → Tab "Khối ngoại" → Xem top mua/bán ròng ngày hôm trước
2. Vietstock → Thị trường → Giao dịch khối ngoại
3. Chú ý mã bị bán ròng liên tiếp dù giá vẫn tăng → **Dấu hiệu phân phối nguy hiểm**

### 3.2 Phân tích dòng tiền ngành (Heatmap)

Chọn đúng **ngành đang hút tiền** quan trọng ngang với chọn mã.

```
Quy trình:
1. Mở FireAnt/Vietstock → Heatmap ngành
2. Xác định nhóm nào tăng đồng thuận, volume cao (3–5 phiên liên tiếp)
3. Chỉ mua mã trong nhóm đang được dòng tiền ủng hộ
4. Tránh "mã cô đơn" tăng khi cả ngành giảm — dễ bị đảo chiều
```

**Luân chuyển ngành điển hình trong chu kỳ phục hồi:**
> Ngân hàng → Thép/Vật liệu → BĐS → Chứng khoán → Tiêu dùng

### 3.3 Phân tích thanh khoản toàn thị trường

| Mức thanh khoản HOSE | Ý nghĩa |
|----------------------|---------|
| > 25,000 tỷ/phiên | Dòng tiền mạnh, thị trường risk-on |
| 15,000–25,000 tỷ/phiên | Bình thường |
| < 15,000 tỷ/phiên | Dòng tiền yếu, thận trọng |
| Giảm đột ngột >30% so hôm trước | Cảnh báo phân phối hoặc thiếu cầu |

---

## BƯỚC 4: PHÂN TÍCH CƠ BẢN DOANH NGHIỆP

**Thời gian:** 30–45 phút cho lần đầu phân tích một mã  
**Công cụ:** Vietstock Finance, CafeF, SSC công bố thông tin, báo cáo CTCK

Đây là tầng **quan trọng nhất** và thường bị bỏ qua nhất. Gồm 4 mảng:

---

### 4.1 Đánh Giá Tăng Trưởng & Lợi Nhuận

**Câu hỏi cần trả lời:**
- EPS đang tăng hay giảm trong 4 quý gần nhất?
- Doanh thu tăng từ tăng giá bán hay tăng sản lượng? (sản lượng bền hơn)
- Biên lợi nhuận gộp đang cải thiện hay thu hẹp?
- Lợi nhuận có "chất lượng" không — đến từ kinh doanh cốt lõi hay bán tài sản một lần?

**Bảng kiểm tra nhanh:**

| Chỉ số | Xem ở đâu | Tín hiệu tốt | Cảnh báo |
|--------|----------|-------------|---------|
| Doanh thu YoY | BCTC quý gần nhất | Tăng >10% liên tiếp 2+ quý | Giảm hoặc tăng bất thường |
| LNST YoY | BCTC quý gần nhất | Tăng >15% liên tiếp | Giảm, biến động lớn |
| Gross Margin | BCTC | Tăng hoặc ổn định | Thu hẹp liên tục |
| Net Margin | BCTC | Cải thiện theo thời gian | Giảm dù doanh thu tăng |
| EPS | Vietstock Finance | Tăng đều theo quý | Giảm mạnh 1 quý |

---

### 4.2 Đánh Giá Định Giá (Valuation) — KHÔNG BỎ QUA

Đây là câu trả lời cho câu hỏi: **"Giá hiện tại có phản ánh đúng giá trị không?"**

#### 4.2.1 Các chỉ số định giá cần tính

**P/E (Price-to-Earnings):**
```
P/E = Giá hiện tại / EPS (12 tháng gần nhất)
P/E forward = Giá hiện tại / EPS dự báo năm tới

Ngưỡng tham chiếu Việt Nam:
- <10x: Rất rẻ (nhưng kiểm tra lý do — có bẫy không?)
- 10–13x: Hấp dẫn
- 13–18x: Hợp lý
- >20x: Đắt (cần tăng trưởng EPS rất cao để justify)
```

**P/B (Price-to-Book):**
```
P/B = Giá hiện tại / Giá trị sổ sách trên mỗi cổ phiếu

Ngưỡng theo ngành:
- Ngân hàng: <1.5x = hấp dẫn; >2.5x = đắt
- Sản xuất: <2x = hấp dẫn
- BĐS: <2.5x = hấp dẫn
- Tiêu dùng/Bán lẻ: 3–5x là bình thường nếu ROE cao
```

**PEG (Price/Earnings-to-Growth) — Chỉ số quan trọng nhất:**
```
PEG = P/E / Tốc độ tăng trưởng EPS (%)

- PEG < 0.5: Cực kỳ rẻ so với tăng trưởng → Mua mạnh
- PEG 0.5–1.0: Hấp dẫn
- PEG 1.0–1.5: Hợp lý
- PEG > 2.0: Đắt so với tăng trưởng → Cẩn thận

Ví dụ thực tế:
HPG: P/E 12.2x / EPS tăng 41% = PEG 0.30 → Rất rẻ
MBB: P/E 8x / EPS tăng 24% = PEG 0.33 → Rất rẻ
SAB: P/E 18x / EPS tăng 12% = PEG 1.5 → Đắt (mua vì cổ tức)
VIC: P/E 14x / EPS phụ thuộc BĐS = PEG >2 → Tránh
```

**Dividend Yield (Lợi suất cổ tức):**
```
Yield = Cổ tức dự kiến / Giá hiện tại × 100%

- >8%: Xuất sắc (SAB ~10%, phòng thủ tốt)
- 5–8%: Tốt
- 3–5%: Chấp nhận được
- <3%: Thấp (chỉ mua nếu tăng giá bù)
```

#### 4.2.2 So sánh định giá theo ngành

Định giá phải so sánh **trong cùng ngành**, không so sánh chéo ngành:
- Ngân hàng: So sánh P/B và ROE giữa các ngân hàng
- Thép: So sánh EV/EBITDA và PEG giữa HPG, HSG, NKG
- BĐS: So sánh P/E và Backlog/Giá thị trường giữa VHM, NVL, DIG

---

### 4.3 Đánh Giá Sức Khỏe Tài Chính — BỘ LỌC RỦI RO

Đây là tầng **phòng thủ** — loại bỏ các mã có thể sập bất ngờ dù chart đẹp.

#### 4.3.1 Hiệu suất sinh lời

| Chỉ số | Công thức | Ngưỡng tốt | Ý nghĩa |
|--------|----------|-----------|---------|
| **ROE** | LNST / Vốn CSH | >15% | Sinh lời tốt trên vốn chủ |
| **ROA** | LNST / Tổng TS | Ngân hàng >1%; Sản xuất >7% | Hiệu quả sử dụng tài sản |
| **ROIC** | EBIT(1-t) / Vốn đầu tư | >WACC (thường >12%) | Tạo giá trị thực sự |

**Quy tắc Buffett:** ROE liên tục >20% qua 5 năm = lợi thế cạnh tranh bền vững.

#### 4.3.2 Cấu trúc nợ (Đòn bẩy tài chính)

| Chỉ số | Công thức | Ngưỡng an toàn | Cảnh báo |
|--------|----------|--------------|---------|
| **D/E** | Tổng nợ vay / Vốn CSH | Sản xuất <1.5x; BĐS <2.5x | >3x: Nguy hiểm |
| **Nợ vay / EBITDA** | Nợ tài chính / EBITDA | <3x | >5x: Khó trả nợ |
| **Interest Coverage** | EBIT / Chi phí lãi vay | >5x | <2x: Rủi ro vỡ nợ |
| **Nợ/Tổng tài sản** | Tổng nợ / Tổng TS | <60% | >80%: Rất rủi ro |

**Ví dụ thực chiến:**
```
VIC 2025:
- Nợ vay tăng 50% → D/E tiến gần 3x
- VinFast lỗ lũy kế 32,000 tỷ → Kéo Interest Coverage xuống
→ Tránh VIC dù doanh thu tăng 76%

HPG 2025:
- Nợ ở đỉnh nhưng lãnh đạo xác nhận "2025 là đỉnh nợ"
- Interest Coverage ~4–5x → Vẫn an toàn
- EBITDA 2026F đủ trả nợ → Chấp nhận được
→ Mua tích lũy
```

#### 4.3.3 Chất lượng dòng tiền

Đây là chỉ số thường bị bỏ qua nhất nhưng quan trọng nhất:

```
Dòng tiền hoạt động (CFO) > Lợi nhuận kế toán:
→ Lợi nhuận "thật", tiền về được thực sự

CFO < Lợi nhuận kế toán nhiều kỳ liên tiếp:
→ Cảnh báo: Doanh thu ghi nhận nhưng chưa thu được tiền
→ Rủi ro nợ xấu khách hàng hoặc ghi nhận sai

Capex/Doanh thu:
→ Cao khi đang đầu tư mở rộng (chấp nhận được ngắn hạn)
→ Cao kéo dài mà không tăng doanh thu → Đầu tư kém hiệu quả

Free Cash Flow (FCF) = CFO - Capex:
→ FCF > 0 và tăng: Công ty sinh tiền mặt thực sự → Rất tốt
→ FCF âm liên tục: Phụ thuộc vay nợ → Rủi ro
```

#### 4.3.4 Bảng cân đối kế toán — 3 điểm kiểm tra nhanh

1. **Tiền mặt + Đầu tư ngắn hạn:** Có đủ thanh khoản để hoạt động 6–12 tháng không?
2. **Hàng tồn kho:** Tăng nhanh hơn doanh thu → Hàng không bán được
3. **Phải thu khách hàng:** Tăng nhanh hơn doanh thu → Bán hàng nhưng khó thu tiền

---

### 4.4 Đánh Giá Câu Chuyện Doanh Nghiệp (Business Narrative)

Chart đẹp + số tốt mà không có "câu chuyện" → Dòng tiền sẽ không duy trì.

**Câu hỏi cần trả lời:**
- Doanh nghiệp đang ở **giai đoạn nào** của chu kỳ ngành? (tăng tốc/bão hòa/suy giảm)
- Có **catalyst** gì trong 3–12 tháng tới? (hợp đồng mới, dự án mới, cổ tức, buyback)
- **Lợi thế cạnh tranh** là gì? (thị phần, công nghệ, chi phí thấp, thương hiệu)
- **Rủi ro đặc thù** của mã này là gì? (giá nguyên liệu, cạnh tranh, pháp lý)

**Nguồn để đọc câu chuyện:**
- Nghị quyết ĐHĐCĐ và kế hoạch kinh doanh năm: SSC công bố thông tin
- Tin tức doanh nghiệp: CafeF, Tinnhanhchungkhoan, 24hmoney
- Báo cáo cập nhật CTCK: SSI Research, BVSC, BSC, ACBS

---

## BƯỚC 5: PHÂN TÍCH KỸ THUẬT & TIMING

**Thời gian:** 15–20 phút sau khi đã qua 4 tầng trên  
**Công cụ:** FireAnt (chart), Vietstock (chart + chỉ báo), TradingView

> **Nguyên tắc quan trọng:** Kỹ thuật chỉ là **công cụ tìm điểm vào/ra**, không phải lý do mua. Đừng mua vì chart đẹp khi cơ bản yếu.

### 5.1 Phân Tích Xu Hướng (Multi-Timeframe)

Phân tích theo thứ tự từ lớn đến nhỏ:

```
Bước 1: Xem chart TUẦN (Weekly)
→ Xác định xu hướng lớn: Uptrend / Downtrend / Sideway
→ Tìm vùng hỗ trợ/kháng cự lớn (swing high/low)
→ Chỉ mua khi weekly đang uptrend hoặc vừa breakout

Bước 2: Xem chart NGÀY (Daily) — Khung chính
→ Xác nhận xu hướng ngắn hạn đồng chiều weekly
→ Tìm pattern (Breakout, Pullback, Reversal)
→ Xác định điểm vào, SL, TP cụ thể

Bước 3: Xem chart 4H hoặc 1H (nếu cần)
→ Tìm timing vào lệnh chính xác hơn
→ Tránh buy đỉnh ngày bằng cách xem 4H
```

### 5.2 Đường Trung Bình Động (Moving Averages)

| Đường MA | Ý nghĩa | Cách dùng |
|----------|---------|----------|
| **EMA20** | Xu hướng ngắn hạn | Giá trên EMA20 = short-term bullish; Test EMA20 = điểm mua |
| **EMA50** | Xu hướng trung hạn | Giá trên EMA50 = medium-term bullish; Hỗ trợ mạnh |
| **SMA200** | Xu hướng dài hạn | Giá trên SMA200 = uptrend lớn; Dưới = bear market |
| **Golden Cross** | EMA20 cắt lên EMA50 | Tín hiệu mua trung hạn |
| **Death Cross** | EMA20 cắt xuống EMA50 | Tín hiệu bán / tránh mua |

**Quy tắc sử dụng MA:**
```
BUY SETUP:
- Giá hồi về test EMA20 (trong uptrend) → Entry
- EMA20 > EMA50 > SMA200 (3 đường sắp xếp tốt) → Mua mạnh hơn

TRÁNH:
- Giá dưới SMA200 → Không swing trade, chỉ scalp nếu có
- Death Cross vừa hình thành → Tránh mua, chờ xác nhận
```

### 5.3 Các Chỉ Báo Bổ Sung

**RSI (Relative Strength Index):**
```
- RSI < 30: Oversold → Tín hiệu mua tiềm năng (xác nhận thêm)
- RSI 40–60: Trung tính, xu hướng chưa rõ
- RSI > 70: Overbought → Không đuổi mua, đợi hồi
- RSI > 80: Rất overbought → Có thể short-term bán

Divergence (phân kỳ):
- Giá tăng nhưng RSI giảm → Bearish divergence → Cảnh báo đảo chiều
- Giá giảm nhưng RSI tăng → Bullish divergence → Cơ hội mua
```

**MACD:**
```
- MACD line cắt lên Signal line (Golden Cross MACD) → Tín hiệu mua
- MACD line cắt xuống Signal line (Death Cross MACD) → Tín hiệu bán
- Histogram dương và tăng → Momentum tăng mạnh
- Histogram dương nhưng giảm → Momentum đang yếu dần → Chuẩn bị thoát
```

**Volume:**
```
Breakout có Volume cao gấp 1.5–2x bình quân → Xác nhận breakout thật
Breakout Volume thấp → Fake breakout, không đáng tin

Volume tăng trong ngày giảm → Phân phối, tránh mua
Volume giảm trong nhịp hồi (pullback) → Bình thường, có thể mua
```

**Bollinger Bands:**
```
- Giá chạm dải dưới BB + RSI < 35 → Oversold setup, tìm mua
- Giá phá vỡ dải trên BB với volume cao → Breakout mạnh
- BB thu hẹp (squeeze) → Chuẩn bị biến động lớn, chờ hướng
```

### 5.4 Các Pattern Phổ Biến Trong TTCK Việt Nam

**Các Pattern MUA (Bullish):**

```
1. PULLBACK TO EMA20 (Phổ biến nhất)
   - Xu hướng uptrend rõ
   - Giá hồi về test EMA20 không phá
   - Volume nhỏ trong nhịp hồi, tăng khi bật lên
   → Entry: Khi nến bật từ EMA20
   → SL: Dưới EMA20 hoặc đáy nến xác nhận

2. BREAKOUT (Phá vỡ kháng cự)
   - Giá sideway tích lũy lâu ngày
   - Đột phá kháng cự với volume tăng mạnh
   → Entry: Ngay khi breakout hoặc retest vùng phá vỡ
   → SL: Dưới vùng breakout

3. DOUBLE BOTTOM / W PATTERN
   - Giá tạo 2 đáy tương đương, đáy sau không thấp hơn
   - RSI bullish divergence
   → Entry: Khi vượt đường cổ nối 2 đáy
   → SL: Dưới đáy thứ 2

4. CUP AND HANDLE
   - Tạo hình chữ U dài (cup), sau đó hồi nhẹ (handle)
   - Breakout khỏi handle với volume
   → Entry: Vượt đường kháng cự handle
```

**Các Pattern TRÁNH (Bearish):**

```
1. PHÂN PHỐI (Distribution Top)
   - Giá tăng mạnh lên đỉnh
   - Volume cao nhưng giá không tăng thêm
   - Khối ngoại/tự doanh bán ròng
   → Không mua; nếu đang giữ → cân nhắc thoát

2. FAKE BREAKOUT
   - Giá vượt kháng cự nhưng volume thấp
   - Không giữ được trên vùng breakout >2 phiên
   → Tránh mua khi volume không xác nhận

3. HEAD AND SHOULDERS
   - 3 đỉnh, đỉnh giữa cao nhất
   - Phá vỡ đường cổ (neckline) xuống
   → Tín hiệu bán, tránh mua
```

---

## BƯỚC 6: XÁC ĐỊNH ENTRY, STOP LOSS, TAKE PROFIT

Sau khi hoàn thành 5 tầng phân tích, bước này là **cơ học** — không cần đoán, chỉ cần thực thi theo kế hoạch.

### 6.1 Tính Risk:Reward trước khi vào lệnh

```
Risk:Reward = (TP - Entry) / (Entry - SL)

Tối thiểu R:R = 1:2
Lý tưởng = 1:2.5 đến 1:3

Ví dụ HPG:
- Entry: 61,000 VND
- SL: 58,000 VND → Risk = 3,000 VND/cp (4.9%)
- TP: 70,000 VND → Reward = 9,000 VND/cp (14.8%)
- R:R = 9,000/3,000 = 3.0 → Tốt, vào lệnh

Nếu R:R < 1:2 → Bỏ qua lệnh đó, chờ setup tốt hơn.
```

### 6.2 Đặt Stop Loss theo cấu trúc giá

**Nguyên tắc:** SL đặt theo **cấu trúc** (dưới hỗ trợ, dưới đáy setup), KHÔNG đặt theo % cơ học.

```
SL đúng: Dưới vùng hỗ trợ gần nhất (EMA20, đáy nến, đáy swing)
SL sai: "Tôi chịu lỗ tối đa 5% nên đặt SL -5%" → Không có logic cấu trúc

Sau khi có SL theo cấu trúc, kiểm tra:
- Khoảng cách SL có quá lớn không? (>8% cho swing → cân nhắc lại)
- Với khoảng SL đó, TP tối thiểu có đạt R:R 1:2 không?
- Nếu không → Bỏ lệnh, chờ entry tốt hơn
```

**Tham chiếu vùng SL:**

| Loại setup | SL đặt ở đâu |
|-----------|------------|
| Pullback EMA20 | Dưới EMA20 hoặc dưới đáy nến xác nhận |
| Breakout | Dưới vùng phá vỡ (cũ là kháng cự, nay là hỗ trợ) |
| Double Bottom | Dưới đáy thứ 2 |
| Đỉnh thị trường/ngành khó | SL chặt hơn: -4% đến -5% |

### 6.3 Đặt Take Profit theo kháng cự

```
TP1 (50% vị thế): Kháng cự gần nhất (đỉnh swing cũ, vùng tập trung volume)
TP2 (50% còn lại): Kháng cự xa hơn hoặc mục tiêu Fibonacci

Cách quản lý sau khi TP1:
- Dời SL lên Entry (break-even)
- Để phần còn lại chạy theo trailing stop
```

### 6.4 Tính Size Vị Thế (Position Sizing)

Đây là bước **quyết định sự tồn tại của tài khoản**:

```
Quy tắc 1%:
Số tiền tối đa chấp nhận lỗ/lệnh = 1–2% tổng vốn

Công thức:
Số cổ phiếu = (Vốn × % chấp nhận lỗ) / (Entry - SL)

Ví dụ với 10 triệu đồng:
- Chấp nhận lỗ tối đa 1% = 100,000 VND/lệnh
- Entry HPG: 61,000 | SL: 58,000 → Risk/cp = 3,000
- Số cổ phiếu = 100,000 / 3,000 = 33 cp (khoảng 2 triệu đồng)
→ Size vừa phải, không oversize

Với vốn 10 triệu, không nên để 1 lệnh chiếm >30% vốn.
```

---

## BƯỚC 7: KIỂM TRA SỰ KIỆN DOANH NGHIỆP

Trước khi bấm mua, kiểm tra nhanh lịch sự kiện trong 7–14 ngày tới:

**Nguồn:** SSC công bố thông tin (congbothongtin.ssc.gov.vn), hsx.vn/tin-tuc

### 7.1 Bảng sự kiện & hành động

| Sự kiện | Rủi ro | Hành động |
|---------|--------|----------|
| **Công bố KQKD quý** (trong <5 ngày) | Cao — giá có thể gap mạnh cả 2 chiều | Không vào lệnh mới; đợi sau công bố |
| **Ngày chốt quyền cổ tức** | Giá giảm bằng mệnh giá cổ tức sau ngày chốt | Tính vào TP nếu đang giữ |
| **ĐHĐCĐ thường niên** | Kế hoạch năm mới tác động tâm lý | Đọc nghị quyết trước, sau đó giao dịch |
| **Phát hành thêm cổ phiếu / ESOP** | Pha loãng → Giá giảm | Tránh mua khi có tin phát hành |
| **Thay CEO / Chủ tịch đột ngột** | Bất định cao | Chờ ít nhất 3–5 phiên, đọc bối cảnh |
| **Bị điều tra / vi phạm công bố** | Rủi ro rất cao | Thoát ngay nếu đang giữ |
| **Insider mua lớn** | Tín hiệu tốt — nội bộ lạc quan | Ủng hộ luận điểm mua |

### 7.2 Quy tắc "Buy the rumor, Sell the news"

```
Trước sự kiện tích cực (KQKD tốt được kỳ vọng):
- Giá thường tăng TRƯỚC khi tin ra
- Khi tin ra dù tốt → Giá thường giảm (đã "priced-in")
→ Không mua đuổi ngay trước sự kiện nếu giá đã tăng mạnh rồi

Sau sự kiện tích cực bất ngờ:
- Tin tốt KHÔNG được kỳ vọng → Giá gap up mạnh
→ Đây mới là cơ hội thật sự
```

---

## BƯỚC 8: SCORECARD TỔNG HỢP & RA QUYẾT ĐỊNH

Sau khi hoàn thành 7 bước, điền vào bảng này:

### Template Scorecard Phân Tích Mã ___

```
Ngày phân tích: ___________
Mã cổ phiếu: ___________
Giá hiện tại: ___________

TẦNG 1 — VĨ MÔ TOÀN CẦU
[ ] DXY < 103 (thuận lợi)
[ ] VIX < 20 (rủi ro thấp)
[ ] Không có sự kiện Fed/CPI trong 48h
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 2 — VĨ MÔ VIỆT NAM
[ ] GDP dự báo >6.5%
[ ] Lãi suất NHNN ổn định hoặc giảm
[ ] Tỷ giá ổn định (<2% biến động ytd)
[ ] Catalyst tích cực (nâng hạng, đầu tư công...)
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 3 — DÒNG TIỀN
[ ] Khối ngoại mua ròng 3+ phiên gần đây
[ ] Ngành của mã đang được dòng tiền ủng hộ
[ ] Thanh khoản toàn thị trường >20,000 tỷ
[ ] Tự doanh không bán ròng mạnh
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 4A — TĂNG TRƯỞNG & LỢI NHUẬN
[ ] Doanh thu tăng >10% YoY
[ ] LNST tăng >15% YoY
[ ] Biên gộp ổn định hoặc cải thiện
[ ] Lợi nhuận từ hoạt động cốt lõi (không phải bán tài sản)
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 4B — ĐỊNH GIÁ
P/E TTM: ___  P/E Forward: ___  PEG: ___
P/B: ___  Dividend Yield: ___%
[ ] PEG < 1.5 (không đắt so với tăng trưởng)
[ ] P/B hợp lý theo ngành
[ ] Có upside >15% đến giá mục tiêu CTCK
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 4C — SỨC KHỎE TÀI CHÍNH
ROE: ___%  ROA: ___%  D/E: ___x
Interest Coverage: ___x  FCF: dương/âm
[ ] ROE > 15%
[ ] D/E < 2x (hoặc hợp lý ngành)
[ ] Interest Coverage > 3x
[ ] FCF dương hoặc có lộ trình dương
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 4D — CÂU CHUYỆN DOANH NGHIỆP
[ ] Có catalyst rõ ràng trong 3–12 tháng
[ ] Lợi thế cạnh tranh rõ ràng
[ ] Không có rủi ro pháp lý hay điều tra
[ ] Ban lãnh đạo đáng tin cậy (track record tốt)
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

TẦNG 5 — KỸ THUẬT
[ ] Xu hướng uptrend (giá trên EMA50, EMA20 > EMA50)
[ ] RSI 40–65 (không overbought)
[ ] MACD histogram dương hoặc sắp Golden Cross
[ ] Volume xác nhận setup
[ ] R:R ≥ 1:2
Pattern nhận diện: ___________
Entry: ___  SL: ___  TP1: ___  TP2: ___
Nhận xét: ___________  Điểm: 🟢/🟡/🔴

SỰ KIỆN DOANH NGHIỆP (7–14 ngày tới)
[ ] Không có KQKD / ĐHĐCĐ trong 5 ngày tới
[ ] Không có tin phát hành thêm / thay lãnh đạo đột ngột
[ ] Không có rủi ro tin tức lớn

KẾT QUẢ SCORECARD
🟢 (Tốt): ___ / 8 tầng
🟡 (Trung tính): ___ / 8 tầng
🔴 (Xấu): ___ / 8 tầng

QUYẾT ĐỊNH:
- 6–7 tầng 🟢: MUA MẠNH
- 4–5 tầng 🟢: MUA CÓ CHỌN LỌC (size nhỏ)
- 3 tầng 🟢 trở xuống: ĐỨNG NGOÀI / TRÁNH
```

---

## BƯỚC 9: QUẢN TRỊ VỊ THẾ SAU KHI VÀO LỆNH

Vào lệnh chỉ là 30% công việc. 70% còn lại là quản lý sau đó.

### 9.1 Theo dõi và cập nhật luận điểm

```
Hàng ngày kiểm tra:
- Giá có đang đi theo kỳ vọng không?
- Có tin tức bất ngờ nào thay đổi câu chuyện không?
- Dòng tiền khối ngoại có thay đổi chiều không?

Thoát lệnh khi:
1. SL bị chạm → Thoát ngay, không tiếc
2. Luận điểm bị phá vỡ (dù chưa chạm SL)
   Ví dụ: Mua vì KQKD tốt, nhưng công ty vừa thông báo điều tra
   → Thoát không cần chờ SL
3. Giá không đi đúng sau 10 phiên → Xem xét thoát để giải phóng vốn
```

### 9.2 Nhật ký giao dịch — Bắt buộc

| Trường | Nội dung |
|--------|---------|
| Ngày vào | |
| Mã | |
| Giá vào / SL / TP | |
| Lý do vào (từng tầng) | |
| Ngày thoát | |
| Giá thoát / P&L | |
| Bài học rút ra | |

> **Không có nhật ký = Không tiến bộ được.** Trader chuyên nghiệp xem lại 100% lệnh đã thực hiện.

---

## PHỤ LỤC: NGUỒN DỮ LIỆU CHO TỪNG BƯỚC

| Bước | Công cụ/Nguồn | URL |
|------|--------------|-----|
| Vĩ mô toàn cầu | TradingView, Investing.com | tradingview.com, investing.com/economic-calendar |
| Vĩ mô Việt Nam | NHNN, SSI Research | sbv.gov.vn, ssi.com.vn/research |
| Dòng tiền khối ngoại | FireAnt, Vietstock | fireant.vn/analysis, vietstock.vn |
| Heatmap ngành | FireAnt, Vietstock | fireant.vn/analysis |
| BCTC doanh nghiệp | Vietstock Finance, CafeF | finance.vietstock.vn |
| P/E, P/B, ROE, ROA | Vietstock Finance | finance.vietstock.vn |
| Công bố thông tin | SSC, HOSE | congbothongtin.ssc.gov.vn, hsx.vn/tin-tuc |
| Tin tức doanh nghiệp | CafeF, 24hmoney, TNCK | cafef.vn, 24hmoney.vn, tinnhanhchungkhoan.vn |
| Báo cáo CTCK | SSI, BVSC, BSC, ACBS | ssi.com.vn/research |
| Thực hiện lệnh | DNSE Entrade X | dnse.com.vn |

---

*Tài liệu xây dựng từ backbone trading và phân tích thực chiến tháng 4/2026.*  
*Cập nhật lần cuối: 02/04/2026*
