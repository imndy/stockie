# Stock Analysis Flow — vnstock3

## Cấu trúc thư mục

```
draft/
├── analyze.py          ← script chính
├── input/
│   └── stocks.csv      ← danh sách mã cổ phiếu (cột: ticker)
└── output/
    ├── report_YYYYMMDD_HHMMSS.xlsx   ← báo cáo Excel nhiều sheet
    └── report_YYYYMMDD_HHMMSS.txt    ← báo cáo văn bản
```

## Cách chạy

```bash
# Kích hoạt môi trường ảo (Windows)
.venv\Scripts\activate

# Chạy phân tích
python draft/analyze.py
```

## File input — `draft/input/stocks.csv`

Chỉ cần 1 cột tên `ticker`:

```csv
ticker
VNM
VCB
FPT
...
```

## Output

| Sheet Excel           | Nội dung                          |
|-----------------------|-----------------------------------|
| Tóm Tắt               | Tổng hợp: vốn hóa, P/E, P/B, EPS, ROE, ROA |
| Bảng Giá              | Giá hiện tại toàn bộ danh sách    |
| `<TICKER>_TongQuan`   | Thông tin tổng quan công ty       |
| `<TICKER>_HoSo`       | Mô tả / hồ sơ công ty            |
| `<TICKER>_CoDong`     | Cổ đông lớn                       |
| `<TICKER>_LanhDao`    | Ban lãnh đạo                      |
| `<TICKER>_KQKD`       | Kết quả kinh doanh (quý)          |
| `<TICKER>_CDKT`       | Bảng cân đối kế toán (quý)        |
| `<TICKER>_LCTT`       | Lưu chuyển tiền tệ (quý)          |
| `<TICKER>_ChiSo`      | Chỉ số tài chính (P/E, P/B, ROE…) |
| `<TICKER>_LichSuGia`  | Lịch sử giá 1 năm gần nhất        |

## Dependencies

- `vnstock3` — dữ liệu chứng khoán Việt Nam
- `pandas`   — xử lý dữ liệu
- `openpyxl` / `xlsxwriter` — xuất Excel
