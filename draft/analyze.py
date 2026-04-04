"""
Stock Analysis Flow — two-pipeline design
Usage:
  python analyze.py --mode daily       # cập nhật giá, chỉ số, tin tức
  python analyze.py --mode quarterly   # cập nhật tài chính, công ty
  python analyze.py --mode full        # tất cả (default)

Input : draft/input/stocks.csv  (cột 'ticker')
Output:
  draft/output/per_ticker/<TICKER>.md  ← file duy nhất / mã, update in-place
  draft/output/daily/YYYYMMDD/         ← summary.md  daily_*.xlsx
  draft/output/quarterly/YYYYQQ/       ← summary.md  quarterly_*.xlsx

Mỗi file per_ticker dng sentinel:
  <!-- BEGIN:DAILY -->    ... <!-- END:DAILY -->
  <!-- BEGIN:QUARTERLY --> ... <!-- END:QUARTERLY -->
Khi run daily   → chỉ replace block DAILY
Khi run quarterly → chỉ replace block QUARTERLY
Nếu ticker chưa có file → tự động run FULL

Sources:
  KBS  → company info + financials
  VCI  → price history, price board, ratio_summary, trading_stats
"""

import argparse
import time
import warnings
from datetime import datetime, date
from pathlib import Path

import pandas as pd

RATE_LIMIT_DELAY_DAILY     = 4   # s giữa mỗi mã — daily  (~5 calls/mã)
RATE_LIMIT_DELAY_QUARTERLY = 7   # s giữa mỗi mã — quarterly (~9 calls/mã)
RATE_LIMIT_RETRY_WAIT      = 65  # s chờ khi bị rate limit

warnings.filterwarnings("ignore")

SOURCE_COMPANY = "KBS"   # company info + financials
SOURCE_QUOTE   = "VCI"   # price history, price board, ratio_summary, trading_stats

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
INPUT_CSV = BASE_DIR / "input" / "stocks.csv"


# Shared per-ticker folder (tồn tại mãi, các mode chỉ update in-place)
PER_TICKER_DIR = BASE_DIR / "output" / "per_ticker"
PER_TICKER_DIR.mkdir(parents=True, exist_ok=True)


def _setup_run_paths(mode: str) -> tuple[Path, Path, Path]:
    """Trả về (subdir, xlsx_path, summary_md) — không có per_ticker_dir (shared)."""
    today = date.today()
    if mode == "daily":
        subdir = BASE_DIR / "output" / "daily" / today.strftime("%Y%m%d")
    elif mode == "quarterly":
        q = (today.month - 1) // 3 + 1
        subdir = BASE_DIR / "output" / "quarterly" / f"{today.year}Q{q}"
    else:
        subdir = BASE_DIR / "output" / "full" / today.strftime("%Y%m%d")

    subdir.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%H%M%S")
    xlsx = subdir / f"{mode}_{today.strftime('%Y%m%d')}_{ts}.xlsx"
    return subdir, xlsx, subdir / "summary.md"


# ── Helpers ────────────────────────────────────────────────────────────────────
def read_tickers(csv_path: Path) -> list[str]:
    df = pd.read_csv(csv_path)
    col = next((c for c in df.columns if c.strip().lower() == "ticker"), None)
    if col is None:
        raise ValueError(f"Không tìm thấy cột 'ticker' trong {csv_path}")
    return [t.strip().upper() for t in df[col].dropna().tolist()]


def safe_call(func, *args, max_retries: int = 2, **kwargs) -> pd.DataFrame:
    """Gọi hàm vnstock. Tự chờ + retry khi rate limit (sys.exit). Trả về DataFrame rỗng nếu lỗi."""
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            if result is None:
                return pd.DataFrame()
            return result if isinstance(result, pd.DataFrame) else pd.DataFrame([result])
        except SystemExit:
            if attempt < max_retries:
                print(f"    [RATE LIMIT] Chờ {RATE_LIMIT_RETRY_WAIT}s rồi thử lại ({attempt + 1}/{max_retries})...")
                time.sleep(RATE_LIMIT_RETRY_WAIT)
            else:
                print(f"    [RATE LIMIT] Bỏ qua sau {max_retries} lần thử.")
                return pd.DataFrame()
        except Exception as exc:
            print(f"    [WARN] {exc}")
            return pd.DataFrame()
    return pd.DataFrame()


# ── Fetch — Daily ────────────────────────────────────────────────────────────
def fetch_trading_stats(stock_vci) -> pd.DataFrame:
    """24-column trading statistics — VCI source only."""
    return safe_call(stock_vci.company.trading_stats)


def fetch_ratio_summary(stock_vci) -> pd.DataFrame:
    """46-column ratio summary — VCI source only."""
    return safe_call(stock_vci.company.ratio_summary)


def fetch_news(stock_kbs) -> pd.DataFrame:
    return safe_call(stock_kbs.company.news)


def fetch_price_history(stock_vci, ticker: str) -> pd.DataFrame:
    """Lịch sử giá 1 năm gần nhất."""
    end   = date.today().strftime("%Y-%m-%d")
    start = date.today().replace(year=date.today().year - 1).strftime("%Y-%m-%d")
    df = safe_call(stock_vci.quote.history, start=start, end=end, interval="1D")
    if not df.empty:
        df.insert(0, "ticker", ticker)
    return df


def fetch_intraday(stock_vci, ticker: str) -> pd.DataFrame:
    """Giao dịch trong ngày (100 lệnh gần nhất)."""
    df = safe_call(stock_vci.quote.intraday)
    if not df.empty:
        df.insert(0, "ticker", ticker)
    return df


def fetch_price_board(vs, tickers: list[str]) -> pd.DataFrame:
    """Bảng giá hiện tại cho toàn bộ danh sách."""
    try:
        board = vs.stock(symbol=tickers[0], source=SOURCE_QUOTE).trading.price_board(
            symbols_list=tickers
        )
        return board if isinstance(board, pd.DataFrame) else pd.DataFrame(board)
    except Exception as exc:
        print(f"  [WARN] price_board: {exc}")
        return pd.DataFrame()


# ── Fetch — Quarterly ────────────────────────────────────────────────────────
def fetch_overview(stock) -> pd.DataFrame:
    return safe_call(stock.company.overview)


def fetch_shareholders(stock) -> pd.DataFrame:
    return safe_call(stock.company.shareholders)


def fetch_officers(stock) -> pd.DataFrame:
    return safe_call(stock.company.officers)


def fetch_subsidiaries(stock) -> pd.DataFrame:
    return safe_call(stock.company.subsidiaries)


def fetch_affiliate(stock) -> pd.DataFrame:
    return safe_call(stock.company.affiliate)


def fetch_income_statement(stock) -> pd.DataFrame:
    return safe_call(stock.finance.income_statement, period="quarter")


def fetch_balance_sheet(stock) -> pd.DataFrame:
    return safe_call(stock.finance.balance_sheet, period="quarter")


def fetch_cash_flow(stock) -> pd.DataFrame:
    return safe_call(stock.finance.cash_flow, period="quarter")


def fetch_ratio(stock) -> pd.DataFrame:
    return safe_call(stock.finance.ratio, period="quarter")


# ── Flatten / strip helpers ───────────────────────────────────────────────────
def _flat_df(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns, strip timezone from datetimes, reset index nếu cần."""
    if df is None or df.empty:
        return pd.DataFrame([{"info": "Không có dữ liệu"}])
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" | ".join(str(c) for c in col).strip() for col in df.columns]
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    # Strip timezone from all datetime columns (Excel requirement)
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            try:
                df[col] = df[col].dt.tz_localize(None)
            except TypeError:
                df[col] = df[col].dt.tz_convert(None)
    return df


# ── Write Excel ────────────────────────────────────────────────────────────────
def write_excel(sheets: dict[str, pd.DataFrame], path: Path) -> None:
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        wb = writer.book
        hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1F4E79",
                                 "font_color": "white", "border": 1})

        for sheet_name, df in sheets.items():
            df = _flat_df(df)
            sn = sheet_name[:31]
            df.to_excel(writer, sheet_name=sn, index=False, startrow=1, header=False)
            ws = writer.sheets[sn]
            for col_idx, col_name in enumerate(df.columns):
                ws.write(0, col_idx, str(col_name), hdr_fmt)
            for col_idx, col_name in enumerate(df.columns):
                col_len = max(
                    len(str(col_name)),
                    df[col_name].apply(lambda x: len(str(x)) if x is not None else 0).max() if not df.empty else 0,
                )
                ws.set_column(col_idx, col_idx, min(col_len + 2, 45))

    print(f"  Excel  → {path}")


# ── Markdown helpers ──────────────────────────────────────────────────────────
def _df_to_md(df: pd.DataFrame, max_rows: int = 30) -> str:
    """Convert DataFrame to Markdown table. Giới hạn max_rows để kiểm soát token."""
    if df is None or df.empty:
        return "_Không có dữ liệu_"
    df = df.head(max_rows).copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" | ".join(str(c) for c in col).strip() for col in df.columns]
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            try:
                df[col] = df[col].dt.tz_localize(None)
            except TypeError:
                df[col] = df[col].dt.tz_convert(None)
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: str(x)[:120] + "…" if isinstance(x, str) and len(x) > 120 else x
        )
    return df.to_markdown(index=False)


def _df_to_md_kv(df: pd.DataFrame) -> str:
    """Wide single-row DataFrame → key/value Markdown table (dễ đọc hơn cho LLM)."""
    if df is None or df.empty:
        return "_Không có dữ liệu_"
    row = df.iloc[0]
    lines = ["| Chỉ tiêu | Giá trị |", "| --- | --- |"]
    for k, v in row.items():
        v_str = str(v)[:160] + "…" if isinstance(v, str) and len(v) > 160 else str(v)
        lines.append(f"| {k} | {v_str} |")
    return "\n".join(lines)


def _ov_field(overview: pd.DataFrame, *keys: str) -> str:
    """Lấy giá trị field đầu tiên khớp từ overview DataFrame."""
    if overview.empty:
        return ""
    row = overview.iloc[0]
    for k in keys:
        matches = [c for c in overview.columns if k.lower() in c.lower()]
        if matches:
            return str(row[matches[0]])
    return ""


# ── Write Markdown summary ────────────────────────────────────────────────────
def write_markdown_summary(
    detail_map: dict,
    price_board: pd.DataFrame,
    path: Path,
    mode: str,
) -> None:
    today_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines: list[str] = [
        f"# Tổng hợp cổ phiếu — {mode.upper()}",
        f"**Ngày:** {today_str}  |  **Số mã:** {len(detail_map)}  |  **Pipeline:** `{mode}`",
        "",
        "---",
        "",
        "## Bảng so sánh",
        "",
    ]

    rows = []
    for ticker, frames in detail_map.items():
        ov = frames.get("Tổng quan",           pd.DataFrame())
        ts = frames.get("Thống kê giao dịch",  pd.DataFrame())
        rs = frames.get("Tóm tắt chỉ số",      pd.DataFrame())
        ic = frames.get("Kết quả kinh doanh",  pd.DataFrame())

        row: dict = {"Mã": ticker}

        if not ov.empty:
            row["Tên công ty"]   = _ov_field(ov, "short_name", "company_name")
            row["Ngành"]         = _ov_field(ov, "industry")
            row["Vốn ĐL (tỷ)"]  = _ov_field(ov, "charter_capital")

        if not ts.empty:
            ts_r = ts.iloc[0]
            for label, keys in [
                ("Giá đóng cửa",  ["match_price", "close_price", "price"]),
                ("Thay đổi (%)",  ["price_change_pct"]),
                ("KL khớp",       ["total_volume"]),
                ("52W High",      ["high_price_1y", "highest_price"]),
                ("52W Low",       ["low_price_1y",  "lowest_price"]),
                ("Room NN",       ["foreign_room"]),
            ]:
                for k in keys:
                    m = [c for c in ts.columns if k.lower() in c.lower()]
                    if m:
                        row[label] = ts_r[m[0]]
                        break

        if not rs.empty:
            rs_r = rs.iloc[0]
            for label, keys in [
                ("P/E",              ["pe"]),
                ("P/B",              ["pb"]),
                ("EPS",              ["eps"]),
                ("ROE",              ["roe"]),
                ("ROA",              ["roa"]),
                ("Biên LN gộp",      ["gross_margin"]),
                ("Tăng trưởng DT",   ["revenue_growth"]),
                ("Tăng trưởng LN",   ["net_profit_growth"]),
            ]:
                for k in keys:
                    m = [c for c in rs.columns if k.lower() in c.lower()]
                    if m:
                        row[label] = rs_r[m[0]]
                        break

        rows.append(row)

    lines.append(_df_to_md(pd.DataFrame(rows), max_rows=200))

    if not price_board.empty:
        lines += ["", "---", "", "## Bảng giá", "", _df_to_md(price_board, max_rows=100)]

    lines += ["", "---", "", "## Chi tiết từng mã", ""]
    for ticker in detail_map:
        lines.append(f"- [{ticker}](per_ticker/{ticker}.md)")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  MD summary → {path}")


# ── Per-ticker Markdown builders ─────────────────────────────────────────────
BEGIN_DAILY     = "<!-- BEGIN:DAILY -->"
END_DAILY       = "<!-- END:DAILY -->"
BEGIN_QUARTERLY = "<!-- BEGIN:QUARTERLY -->"
END_QUARTERLY   = "<!-- END:QUARTERLY -->"


def _build_daily_block(frames: dict) -> str:
    """Trả về nội dung block DAILY (không bao gồm sentinel)."""
    ts_kv = frames.get("Thống kê giao dịch", pd.DataFrame())
    rs_kv = frames.get("Tóm tắt chỉ số",     pd.DataFrame())
    news  = frames.get("Tin tức",            pd.DataFrame())
    hist  = frames.get("Lịch sử giá",        pd.DataFrame())
    intra = frames.get("Giao dịch trong ngày", pd.DataFrame())

    hist_tail = hist.tail(20) if not hist.empty else pd.DataFrame()

    lines = [
        "## Thống kê giao dịch",
        "",
        _df_to_md_kv(ts_kv),
        "",
        "## Tóm tắt chỉ số tài chính",
        "",
        _df_to_md_kv(rs_kv),
        "",
        "## Tin tức gần nhất",
        "",
        _df_to_md(news, max_rows=10),
        "",
        "## Lịch sử giá (20 phiên gần nhất)",
        "",
        _df_to_md(hist_tail, max_rows=20),
        "",
        "## Giao dịch trong ngày (10 lệnh gần nhất)",
        "",
        _df_to_md(intra, max_rows=10),
        "",
    ]
    return "\n".join(lines)


def _build_quarterly_block(frames: dict) -> str:
    """Trả về nội dung block QUARTERLY (không bao gồm sentinel)."""
    ov = frames.get("Tổng quan", pd.DataFrame())

    founded     = _ov_field(ov, "founded_date", "established")
    listing_d   = _ov_field(ov, "listing_date")
    charter_cap = _ov_field(ov, "charter_capital")
    outstanding = _ov_field(ov, "outstanding_share")
    address     = _ov_field(ov, "address")
    website     = _ov_field(ov, "website")
    ceo         = _ov_field(ov, "ceo_name")
    auditor     = _ov_field(ov, "auditor")

    lines = [
        "## Thông tin cơ bản",
        "",
        "| Trường | Giá trị |",
        "| --- | --- |",
        f"| Ngày thành lập | {founded} |",
        f"| Ngày niêm yết | {listing_d} |",
        f"| Vốn điều lệ | {charter_cap} |",
        f"| Cổ phiếu lưu hành | {outstanding} |",
        f"| Tổng giám đốc | {ceo} |",
        f"| Kiểm toán | {auditor} |",
        f"| Địa chỉ | {address[:120] if address else ''} |",
        f"| Website | {website} |",
        "",
    ]

    biz = _ov_field(ov, "business_model")
    if biz:
        lines += ["## Mô hình kinh doanh", "", biz.strip()[:2000], ""]

    hist_text = _ov_field(ov, "history")
    if hist_text:
        lines += ["## Lịch sử phát triển", "", hist_text.strip()[:3000], ""]

    for title, key, max_r in [
        ("Cổ đông lớn",          "Cổ đông lớn",          20),
        ("Ban lãnh đạo",         "Ban lãnh đạo",         20),
        ("Công ty con",          "Công ty con",          30),
        ("Công ty liên kết",     "Công ty liên kết",     20),
        ("Kết quả kinh doanh",   "Kết quả kinh doanh",   40),
        ("Bảng cân đối kế toán", "Bảng cân đối kế toán", 40),
        ("Lưu chuyển tiền tệ",   "Lưu chuyển tiền tệ",   30),
        ("Chỉ số tài chính",     "Chỉ số tài chính",     20),
    ]:
        lines += [f"## {title}", "", _df_to_md(frames.get(key, pd.DataFrame()), max_rows=max_r), ""]

    return "\n".join(lines)


def _replace_block(text: str, begin_tag: str, end_tag: str, new_content: str) -> str:
    """Thay thế nội dung giữa begin_tag và end_tag (bao gồm cả 2 tag)."""
    import re
    pattern = re.compile(
        re.escape(begin_tag) + r".*?" + re.escape(end_tag),
        re.DOTALL,
    )
    replacement = f"{begin_tag}\n{new_content}\n{end_tag}"
    result, count = pattern.subn(replacement, text)
    if count == 0:
        # Tag chưa tồn tại → append vào cuối
        result = text.rstrip() + f"\n\n{replacement}\n"
    return result


def _update_header_ts(text: str, mode: str) -> str:
    """Cập nhật timestamp dòng metadata trong header."""
    import re
    ts_now = datetime.now().strftime("%d/%m/%Y %H:%M")
    tag    = "daily" if mode in ("daily", "full") else "quarterly"
    # Replace dòng "> 📅 ..."
    pattern = re.compile(r"^> .*$", re.MULTILINE)

    def _rebuild(m: re.Match) -> str:
        line = m.group(0)
        # Parse cả 2 giá trị hiện tại
        d_match = re.search(r"Daily: ([\d/: ]+)", line)
        q_match = re.search(r"Quarterly: ([\d/: ]+)", line)
        d_val = d_match.group(1).strip() if d_match else "—"
        q_val = q_match.group(1).strip() if q_match else "—"
        if "daily" in tag:
            d_val = ts_now
        else:
            q_val = ts_now
        if mode == "full":
            d_val = q_val = ts_now
        return f"> 📅 Daily: {d_val}  |  🗂 Quarterly: {q_val}"

    result, count = pattern.subn(_rebuild, text, count=1)
    if count == 0:
        # Chưa có dòng metadata → thêm sau dòng đầu tiên
        lines = result.split("\n")
        insert = f"> 📅 Daily: {'—' if mode not in ('daily','full') else ts_now}  |  🗂 Quarterly: {'—' if mode not in ('quarterly','full') else ts_now}"
        # Tìm dòng trống đầu tiên sau header
        for idx, ln in enumerate(lines):
            if ln.strip() == "" and idx > 0:
                lines.insert(idx, insert)
                break
        result = "\n".join(lines)
    return result


# ── Write Markdown per-ticker ─────────────────────────────────────────────────
def write_markdown_ticker(ticker: str, frames: dict, effective_mode: str) -> None:
    """
    Ghi / cập nhật file output/per_ticker/<TICKER>.md.
    - effective_mode = 'full': tạo/ghi lại toàn bộ file
    - effective_mode = 'daily': chỉ replace block DAILY
    - effective_mode = 'quarterly': chỉ replace block QUARTERLY
    """
    out_path = PER_TICKER_DIR / f"{ticker}.md"

    ov = frames.get("Tổng quan", pd.DataFrame())
    ts = frames.get("Thống kê giao dịch", pd.DataFrame())

    company_name = (
        _ov_field(ov, "short_name", "company_name")
        or (str(ts.iloc[0].get("symbol", ticker)) if not ts.empty else ticker)
    )
    exchange = _ov_field(ov, "exchange") or (str(ts.iloc[0].get("exchange", "")) if not ts.empty else "")
    industry = _ov_field(ov, "industry")

    if effective_mode == "full" or not out_path.exists():
        # ── Tạo file mới từ đầu ──
        ts_now = datetime.now().strftime("%d/%m/%Y %H:%M")
        header = [
            f"# {ticker} — {company_name}",
            f"**Sàn:** {exchange}  |  **Ngành:** {industry}",
            f"> 📅 Daily: {ts_now}  |  🗂 Quarterly: {ts_now}",
            "",
            "---",
            "",
        ]
        daily_section     = [BEGIN_DAILY, "", _build_daily_block(frames), END_DAILY, ""]
        quarterly_section = [BEGIN_QUARTERLY, "", _build_quarterly_block(frames), END_QUARTERLY, ""]
        content = "\n".join(header + daily_section + ["---", ""] + quarterly_section)
    else:
        # ── Update in-place ──
        content = out_path.read_text(encoding="utf-8")
        if effective_mode == "daily":
            content = _replace_block(content, BEGIN_DAILY, END_DAILY, _build_daily_block(frames))
        elif effective_mode == "quarterly":
            content = _replace_block(content, BEGIN_QUARTERLY, END_QUARTERLY, _build_quarterly_block(frames))
        content = _update_header_ts(content, effective_mode)

    out_path.write_text(content, encoding="utf-8")
    action = "created" if effective_mode == "full" else f"updated ({effective_mode})"
    print(f"    MD ticker → {ticker}.md  [{action}]")


# ── Write TXT (quarterly / full only) ────────────────────────────────────────
def write_txt(detail_map: dict, path: Path) -> None:
    lines: list[str] = [
        "=" * 70,
        "  BÁO CÁO PHÂN TÍCH CỔ PHIẾU",
        f"  Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "=" * 70,
    ]
    for ticker, frames in detail_map.items():
        lines += ["\n" + "─" * 70, f"  CHI TIẾT: {ticker}", "─" * 70]
        for section, df in frames.items():
            lines.append(f"\n  >> {section}")
            if isinstance(df, pd.DataFrame) and not df.empty:
                lines.append(df.head(8).to_string(index=False))
            else:
                lines.append("  (Không có dữ liệu)")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Text   → {path}")


# ── Core pipeline ──────────────────────────────────────────────────────────────
def run_pipeline(mode: str) -> None:
    from vnstock import Vnstock

    tickers = read_tickers(INPUT_CSV)
    print(f"\nMode: [{mode.upper()}]  |  Mã ({len(tickers)}): {tickers}\n")

    subdir, xlsx_path, summary_md = _setup_run_paths(mode)
    delay = RATE_LIMIT_DELAY_DAILY if mode == "daily" else RATE_LIMIT_DELAY_QUARTERLY

    vs          = Vnstock()
    detail_map: dict                    = {}
    all_sheets: dict[str, pd.DataFrame] = {}

    # ── Price board — daily + full ──
    price_board = pd.DataFrame()
    if mode in ("daily", "full"):
        print("Đang lấy bảng giá...")
        price_board = fetch_price_board(vs, tickers)
        all_sheets["Bảng Giá"] = price_board

    # ── Per-ticker ──
    for i, ticker in enumerate(tickers):
        # ── New-ticker detection: if no .md exists, force full for this ticker ──
        md_file = PER_TICKER_DIR / f"{ticker}.md"
        is_new  = not md_file.exists()
        effective_mode = "full" if is_new else mode
        if is_new:
            print(f"\n[{ticker}] *** TICKER MỚI — chạy FULL mode ***")
        else:
            print(f"\n[{ticker}]")

        if i > 0:
            # delay depends on heaviest fetch needed for this ticker
            d = RATE_LIMIT_DELAY_QUARTERLY if effective_mode in ("quarterly", "full") else RATE_LIMIT_DELAY_DAILY
            print(f"  (chờ {d}s...)")
            time.sleep(d)

        frames: dict = {}
        kbs = vs.stock(symbol=ticker, source=SOURCE_COMPANY)
        vci = vs.stock(symbol=ticker, source=SOURCE_QUOTE)

        # ── Daily data ──
        if effective_mode in ("daily", "full"):
            frames["Thống kê giao dịch"]   = fetch_trading_stats(vci)
            frames["Tóm tắt chỉ số"]       = fetch_ratio_summary(vci)
            frames["Tin tức"]              = fetch_news(kbs)
            frames["Lịch sử giá"]          = fetch_price_history(vci, ticker)
            frames["Giao dịch trong ngày"] = fetch_intraday(vci, ticker)

            all_sheets[f"{ticker}_TradingStats"] = frames["Thống kê giao dịch"]
            all_sheets[f"{ticker}_RatioSum"]     = frames["Tóm tắt chỉ số"]
            all_sheets[f"{ticker}_TinTuc"]       = frames["Tin tức"]
            all_sheets[f"{ticker}_LichSuGia"]    = frames["Lịch sử giá"]
            all_sheets[f"{ticker}_IntraDay"]     = frames["Giao dịch trong ngày"]

        # ── Quarterly data ──
        if effective_mode in ("quarterly", "full"):
            frames["Tổng quan"]            = fetch_overview(kbs)
            frames["Cổ đông lớn"]          = fetch_shareholders(kbs)
            frames["Ban lãnh đạo"]         = fetch_officers(kbs)
            frames["Công ty con"]          = fetch_subsidiaries(kbs)
            frames["Công ty liên kết"]     = fetch_affiliate(kbs)
            frames["Kết quả kinh doanh"]   = fetch_income_statement(kbs)
            frames["Bảng cân đối kế toán"] = fetch_balance_sheet(kbs)
            frames["Lưu chuyển tiền tệ"]   = fetch_cash_flow(kbs)
            frames["Chỉ số tài chính"]     = fetch_ratio(kbs)

            ic = frames["Kết quả kinh doanh"]
            bs = frames["Bảng cân đối kế toán"]
            cf = frames["Lưu chuyển tiền tệ"]
            rt = frames["Chỉ số tài chính"]

            all_sheets[f"{ticker}_TongQuan"]  = frames["Tổng quan"]
            all_sheets[f"{ticker}_CoDong"]    = frames["Cổ đông lớn"]
            all_sheets[f"{ticker}_LanhDao"]   = frames["Ban lãnh đạo"]
            all_sheets[f"{ticker}_CongTyCon"] = frames["Công ty con"]
            all_sheets[f"{ticker}_LienKet"]   = frames["Công ty liên kết"]
            all_sheets[f"{ticker}_KQKD"]      = ic.head(8) if not ic.empty else ic
            all_sheets[f"{ticker}_CDKT"]      = bs.head(8) if not bs.empty else bs
            all_sheets[f"{ticker}_LCTT"]      = cf.head(8) if not cf.empty else cf
            all_sheets[f"{ticker}_ChiSo"]     = rt.head(8) if not rt.empty else rt

        write_markdown_ticker(ticker, frames, effective_mode)
        detail_map[ticker] = frames

    # ── Output ──
    print("\nĐang xuất báo cáo...")
    write_excel(all_sheets, xlsx_path)
    if mode in ("quarterly", "full"):
        txt_path = xlsx_path.with_suffix(".txt")
        write_txt(detail_map, txt_path)
    write_markdown_summary(detail_map, price_board, summary_md, mode)
    print(f"\nHoàn tất! → {subdir}\nPer-ticker MD → {PER_TICKER_DIR}")
    git_push(mode)


# ── Git auto-push ─────────────────────────────────────────────────────────────
def git_push(mode: str) -> None:
    """Commit và push toàn bộ thay đổi lên GitHub sau khi pipeline chạy xong."""
    import subprocess
    repo_root = BASE_DIR.parent  # Stockie/
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"[auto] {mode} update {ts}"
    print(f"\nGit push: {commit_msg}")
    try:
        def _run(args: list[str]) -> subprocess.CompletedProcess:
            return subprocess.run(
                args, cwd=str(repo_root), capture_output=True, text=True, check=True
            )

        _run(["git", "add", "-A"])
        # Bỏ qua nếu không có gì thay đổi
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root), capture_output=True, text=True
        )
        if not status.stdout.strip():
            print("  (không có thay đổi, bỏ qua push)")
            return
        _run(["git", "commit", "-m", commit_msg])
        _run(["git", "push"])
        print("  Push thành công!")
    except subprocess.CalledProcessError as e:
        print(f"  [WARN] Git push thất bại: {e.stderr.strip()}")


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Phân tích cổ phiếu vnstock")
    parser.add_argument(
        "--mode",
        choices=["daily", "quarterly", "full"],
        default="full",
        help=(
            "daily      = giá + chỉ số + tin tức  (~5 req/mã, ~4s delay)\n"
            "quarterly  = tài chính + công ty      (~9 req/mã, ~7s delay)\n"
            "full       = tất cả                   (default)"
        ),
    )
    args = parser.parse_args()
    run_pipeline(args.mode)


if __name__ == "__main__":
    main()
