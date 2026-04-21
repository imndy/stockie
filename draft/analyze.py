"""
Stock Analysis Flow — two-pipeline design
Usage:
  python analyze.py --mode daily                         # cập nhật giá, chỉ số, tin tức
  python analyze.py --mode quarterly                     # cập nhật tài chính, công ty
  python analyze.py --mode full                          # tất cả (default)

  --force                   bỏ qua gatekeeping ngày/giờ, chạy luôn kệ đã update hay chưa
  --section ticker          chỉ ghi per-ticker .md, bỏ qua bluechip_snapshot
  --section snapshot        chỉ ghi bluechip_snapshot.md, bỏ qua write_markdown_ticker
  --specific <TICKER>       chỉ chạy 1 mã; tự thêm vào stocks.csv nếu chưa có

Examples:
  python analyze.py --mode daily --force
  python analyze.py --mode daily --force --section snapshot
  python analyze.py --mode full  --specific VHC --force

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
  VCI  → price history, price board, ratio_summary, trading_stats,
          news (10 items), events (calendar)
"""

import argparse
import re
import time
import warnings
from collections import deque
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import requests

# ── Rate limiting ──────────────────────────────────────────────────────────────────────────────
# Thấp hơn giới hạn thực tế 3 req — tăng lên nếu có API key cao hơn:
#   Guest: 20/phút  → đặt 18
#   Community (miễn phí sau đăng ký): 60/phút → đặt 57  ← hiện tại
#   Sponsor: 180-600/phút → đặt tương ứng
API_CALLS_PER_MIN = 57  # ← Community 60/min server-side; 25 tracked ≈ 50-60 real
                        #   vì vnstock/tenacity retry nội bộ mỗi failed call thêm 1-2 lần
                        #   → 1 tracked call có thể = 2-3 server requests

RATE_LIMIT_RETRY_WAIT = 65  # s — chẹ nếu vẫn bị bắt sau khi throttle

_CALL_LOG: deque = deque()   # rolling window timestamps
_WINDOW_SEC: float = 61.0    # khớp chính xác server window (60s)


def _throttle() -> None:
    """
    Chủ động đợi nếu sắp vượt API_CALLS_PER_MIN trong 60s.
    Thay thế việc chờ cứng sau khi bị giới hạn.
    """
    now = time.monotonic()
    while _CALL_LOG and now - _CALL_LOG[0] > _WINDOW_SEC:
        _CALL_LOG.popleft()
    if len(_CALL_LOG) >= API_CALLS_PER_MIN:
        wait = _WINDOW_SEC - (now - _CALL_LOG[0]) + 0.5
        if wait > 0:
            print(f"  [PACE] Chủ động đợi {wait:.0f}s — đã dùng {len(_CALL_LOG)}/{API_CALLS_PER_MIN} req/phút...")
            time.sleep(wait)
        now = time.monotonic()
        while _CALL_LOG and now - _CALL_LOG[0] > _WINDOW_SEC:
            _CALL_LOG.popleft()
    _CALL_LOG.append(time.monotonic())

warnings.filterwarnings("ignore")

# ── Patch VCI Company._fetch_data và Finance._get_company_type ────────────────
# VCI GraphQL đôi khi trả về {"errors": [...]} thay vì {"data": {...}}
# → KeyError: 'data' hoặc 'CompanyListingInfo' → crash vs.stock(source="VCI") init
try:
    import vnstock.explorer.vci.company as _vci_co
    _orig_fetch = _vci_co.Company._fetch_data

    def _patched_fetch(self):
        try:
            return _orig_fetch(self)
        except Exception as _e:
            import warnings as _w
            _w.warn(f"[VCI] Company._fetch_data thất bại ({type(_e).__name__}: {_e}); dùng dict rỗng")
            return {}

    _vci_co.Company._fetch_data = _patched_fetch
except Exception:
    pass

try:
    import vnstock.explorer.vci.financial as _vci_fin

    def _patched_get_company_type(self) -> str:
        try:
            from vnstock.explorer.vci.company import Company as _VCICompany
            listing_info = _VCICompany(symbol=self.symbol)._fetch_data().get('CompanyListingInfo') or {}
            icb4 = listing_info.get('icbName4', '')
            # _ICB4_COMTYPE_CODE_MAP từ financial.py
            return _vci_fin._ICB4_COMTYPE_CODE_MAP.get(icb4, 'CT')
        except Exception:
            return 'CT'  # fallback: Công ty thông thường

    _vci_fin.Finance._get_company_type = _patched_get_company_type
except Exception:
    pass
# ──────────────────────────────────────────────────────────────────────────────

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
    """
    Gọi hàm vnstock.
    - _throttle() trước mỗi call — chủ động trước khi bị giới hạn.
    - SystemExit = rate limit bị bắt qua: chờ RATE_LIMIT_RETRY_WAIT rồi retry.
    - Trả về DataFrame rỗng nếu lỗi.
    """
    _throttle()
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
            print(f"    [WARN] {func.__qualname__}: {exc}")
            return pd.DataFrame()
    return pd.DataFrame()


# ── KBS stockinfo/info fallback ────────────────────────────────────────────
_KBS_INFO_URL         = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/info/{symbol}?l=1"
_KBS_NEWS_URL         = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/news/{symbol}?l=1"
_KBS_SECTOR_ALL_URL   = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/sector/all"
_KBS_SECTOR_STOCK_URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment/sector/stock"
_KBS_HEADERS          = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def _build_sector_rs_cache() -> dict:
    """
    Gọi KBS sector API một lần — trả về dict {TICKER: {sector_name, sector_code,
    sector_change, ticker_change, rs_day}} cho toàn bộ mã trong 25 ngành.
    25 lần gọi HTTP, không dùng _throttle() (API khác vnstock).
    """
    result: dict = {}
    try:
        r = requests.get(_KBS_SECTOR_ALL_URL, headers=_KBS_HEADERS, timeout=10)
        if r.status_code != 200:
            print(f"  [WARN] sector/all HTTP {r.status_code}")
            return result
        sectors = r.json()
        for s in sectors:
            code = s.get("code")
            if code is None:
                continue
            try:
                r2 = requests.get(
                    _KBS_SECTOR_STOCK_URL,
                    params={"code": code},
                    headers=_KBS_HEADERS,
                    timeout=10,
                )
                if r2.status_code != 200:
                    continue
                for st in r2.json().get("stocks", []):
                    sym = (st.get("sb") or "").strip().upper()
                    if not sym:
                        continue
                    ch_str = st.get("ch", "")
                    try:
                        t_ch = float(ch_str) if ch_str not in ("", None) else None
                    except (ValueError, TypeError):
                        t_ch = None
                    s_ch = s.get("change")
                    try:
                        s_ch = float(s_ch)
                    except (TypeError, ValueError):
                        s_ch = None
                    rs = round(t_ch - s_ch, 2) if (t_ch is not None and s_ch is not None) else None
                    result[sym] = {
                        "sector_name":   s.get("name", "—"),
                        "sector_code":   code,
                        "sector_change": round(s_ch, 2) if s_ch is not None else None,
                        "ticker_change": round(t_ch, 2) if t_ch is not None else None,
                        "rs_day":        rs,
                    }
            except Exception as exc:
                print(f"  [WARN] sector/stock code={code}: {exc}".encode('ascii', 'replace').decode())
    except Exception as exc:
        print(f"  [WARN] _build_sector_rs_cache: {exc}".encode('ascii', 'replace').decode())
    print(f"  [INFO] Sector RS cache: {len(result)} tickers from {len(sectors) if 'sectors' in dir() else '?'} sectors.")
    return result

def _fetch_kbs_info(ticker: str) -> dict:
    """Gọi KBS stockinfo/info/{ticker} — trả dict thô hoặc {} nếu lỗi."""
    try:
        url = _KBS_INFO_URL.format(symbol=ticker)
        r = requests.get(url, headers=_KBS_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


# ── Fetch — Daily ────────────────────────────────────────────────────────────
def fetch_trading_stats(stock_vci, ticker: str = "") -> pd.DataFrame:
    """Trading statistics — VCI trước, fallback KBS stockinfo/info."""
    df = safe_call(stock_vci.company.trading_stats)
    if not df.empty:
        return df
    if not ticker:
        return df
    info = _fetch_kbs_info(ticker)
    if not info:
        return pd.DataFrame()
    # Map KBS fields → readable names
    row = {
        "symbol":            info.get("SB"),
        "exchange":          info.get("Exchange"),
        "market_cap":        info.get("MC"),
        "52w_high":          info.get("MAP52"),
        "52w_high_date":     info.get("MAD52"),
        "52w_low":           info.get("MIP52"),
        "52w_low_date":      info.get("MID52"),
        "foreign_ownership": info.get("FTO"),
        "dividend":          info.get("DIV"),
        "beta":              info.get("BT"),
        "eps":               info.get("EPS"),
        "eps_forward":       info.get("FEPS"),
        "bvps":              info.get("BVPS"),
        "pe":                info.get("PER"),
        "pb":                info.get("PBR"),
        "price_chg_1m":      info.get("CMCM"),
        "price_chg_ytd":     info.get("CMCY"),
        "price_chg_1m_rank": info.get("CMCME"),
        "price_chg_ytd_rank":info.get("CMCYE"),
        "yield":             info.get("YD"),
        "financial_date":    info.get("FID"),
        "source":            "KBS",
    }
    return pd.DataFrame([{k: v for k, v in row.items() if v is not None}])


def fetch_ratio_summary(stock_vci, ticker: str = "") -> pd.DataFrame:
    """Ratio summary — VCI trước, fallback KBS stockinfo/info."""
    df = safe_call(stock_vci.company.ratio_summary)
    if not df.empty:
        return df
    if not ticker:
        return pd.DataFrame()
    info = _fetch_kbs_info(ticker)
    if not info:
        return pd.DataFrame()
    row = {
        "symbol":   info.get("SB"),
        "pe":       info.get("PER"),
        "pb":       info.get("PBR"),
        "roe":      info.get("ROE"),
        "roe_pct_rank": info.get("ROEP"),
        "roa":      info.get("ROA"),
        "roa_pct_rank": info.get("ROAP"),
        "eps":      info.get("EPS"),
        "bvps":     info.get("BVPS"),
        "beta":     info.get("BT"),
        "dividend": info.get("DIV"),
        "yield":    info.get("YD"),
        "pe_pct_rank": info.get("PERP"),
        "pb_pct_rank": info.get("PBRP"),
        "financial_date": info.get("FID"),
        "source":   "KBS",
    }
    return pd.DataFrame([{k: v for k, v in row.items() if v is not None}])


def fetch_news(stock_vci, stock_kbs=None, ticker: str = "") -> pd.DataFrame:
    """Top 10 tin tức gần nhất — VCI → KBS direct API (20 items) → KBS vnstock."""
    df = safe_call(stock_vci.company.news)
    if df.empty and ticker:
        # KBS direct endpoint trả 20 bài, ưu tiên hơn company.news() (chỉ 1 bài)
        try:
            url = _KBS_NEWS_URL.format(symbol=ticker)
            r = requests.get(url, headers=_KBS_HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    df = pd.DataFrame(data)
                    df.columns = [c.lower() for c in df.columns]
        except Exception:
            pass
    if df.empty and stock_kbs is not None:
        df = safe_call(stock_kbs.company.news)
    return df.head(10) if not df.empty else df


def fetch_events(stock_vci, stock_kbs=None) -> pd.DataFrame:
    """
    Lịch sự kiện — VCI trước, fallback KBS.
    VCI chỉ có: AIS (niêm yết thêm), DIV (cổ tức), ISS (phát hành).
    """
    ev = safe_call(stock_vci.company.events)
    if ev.empty and stock_kbs is not None:
        ev = safe_call(stock_kbs.company.events)
    if ev.empty:
        return ev
    ev = ev.sort_values("public_date", ascending=False)
    keep = [c for c in ["event_list_name", "event_title", "public_date",
                        "record_date", "exright_date", "ratio", "value"] if c in ev.columns]
    return ev[keep].head(15)


def compute_technicals(hist: pd.DataFrame) -> pd.DataFrame:
    """Tính MA5/MA10/EMA20/EMA50, slope MA20, RSI(14), MACD, ATR(14) từ lịch sử giá."""
    if hist.empty or "close" not in hist.columns or len(hist) < 5:
        return pd.DataFrame()
    close = hist["close"].astype(float)
    high  = hist["high"].astype(float) if "high" in hist.columns else close
    low   = hist["low"].astype(float)  if "low"  in hist.columns else close

    # Moving averages
    ma5   = close.rolling(5).mean()
    ma10  = close.rolling(10).mean()
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()

    # Slope MA20: % thay đổi của EMA20 trong 5 phiên gần nhất
    slope_ma20: float | None = None
    if len(ema20) >= 6 and not pd.isna(ema20.iloc[-6]):
        slope_ma20 = round(
            (float(ema20.iloc[-1]) - float(ema20.iloc[-6])) / float(ema20.iloc[-6]) * 100, 2
        )

    # RSI(14) — Wilder smoothing
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, float("nan"))
    rsi      = 100 - 100 / (1 + rs)

    # MACD — EMA12 - EMA26, Signal = EMA9(MACD)
    ema12      = close.ewm(span=12, adjust=False).mean()
    ema26      = close.ewm(span=26, adjust=False).mean()
    macd_line  = ema12 - ema26
    macd_sig   = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist  = macd_line - macd_sig

    # ATR(14) — Average True Range, Wilder smoothing
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr14 = tr.ewm(com=13, adjust=False).mean()

    # Volume stats
    vol_avg60: int | None = None
    if "volume" in hist.columns:
        vol       = hist["volume"].astype(float)
        vol_avg60 = int(round(vol.tail(60).mean()))

    last_close = round(float(close.iloc[-1]),  3)
    e20        = round(float(ema20.iloc[-1]),   3)
    e50        = round(float(ema50.iloc[-1]),   3)
    m5         = round(float(ma5.iloc[-1]),     3) if not pd.isna(ma5.iloc[-1])  else None
    m10        = round(float(ma10.iloc[-1]),    3) if not pd.isna(ma10.iloc[-1]) else None
    rsi_val    = round(float(rsi.iloc[-1]),     1)
    macd_val   = round(float(macd_line.iloc[-1]), 3)
    macd_s_val = round(float(macd_sig.iloc[-1]),  3)
    macd_h_val = round(float(macd_hist.iloc[-1]), 3)
    atr_val    = round(float(atr14.iloc[-1]),   3)

    ema_signal = "TRUNG TÍNH"
    if last_close > e20 > e50:
        ema_signal = "TĂNG (giá > EMA20 > EMA50)"
    elif last_close < e20 < e50:
        ema_signal = "GIẢM (giá < EMA20 < EMA50)"
    elif last_close > e20 and e20 < e50:
        ema_signal = "Vừa vượt EMA20 (chú ý)"

    macd_signal = "MACD > Signal → ĐÀ TĂNG" if macd_val > macd_s_val else "MACD < Signal → ĐÀ XUỐNG"
    if abs(macd_h_val) < 0.01 * abs(macd_val + 0.001):
        macd_signal = "MACD gần cắt Signal (chú ý)"

    row: dict = {
        "Giá đóng cửa":        last_close,
        "MA5":                  m5,
        "MA10":                 m10,
        "EMA20":                e20,
        "EMA50":                e50,
        "Slope MA20 (5p, %)":   slope_ma20,
        "ATR(14)":              atr_val,
        "RSI(14)":              rsi_val,
        "RSI nhận xét":         "Quá mua" if rsi_val > 70 else ("Quá bán" if rsi_val < 30 else "Bình thường"),
        "Tín hiệu EMA":         ema_signal,
        "Giá vs EMA20":         "Trên" if last_close > e20 else "Dưới",
        "Giá vs EMA50":         "Trên" if last_close > e50 else "Dưới",
        "MACD":                 macd_val,
        "MACD Signal":          macd_s_val,
        "MACD Histogram":       macd_h_val,
        "MACD nhận xét":        macd_signal,
        "KL avg 60 phiên":      vol_avg60,
    }
    return pd.DataFrame([{k: v for k, v in row.items() if v is not None}])


def compute_support_resist(
    hist: pd.DataFrame,
    window: int = 5,
    max_levels: int = 3,
    cluster_pct: float = 0.015,
) -> pd.DataFrame:
    """
    Tính vùng hỗ trợ / kháng cự từ swing high/low trên dữ liệu OHLC 90 phiên.

    Thuật toán:
      1. Swing high: high[i] là cực đại trong cửa sổ ±window nến (cả hai phía).
      2. Swing low : low[i]  là cực tiểu trong cửa sổ ±window nến.
      3. Gom cụm (cluster) các mức gần nhau ≤ cluster_pct (1.5%).
         Mức đại diện = trung bình trọng số khối lượng.
      4. Chấm điểm: Σ (0.5 + idx/n) — nến càng mới càng được trọng số cao hơn.
      5. Support  = cluster dưới giá hiện tại, chọn max_levels gần nhất.
         Resistance = cluster trên giá hiện tại, chọn max_levels gần nhất.
    """
    if hist.empty or len(hist) < window * 2 + 5:
        return pd.DataFrame()
    required = {"high", "low", "close"}
    if not required.issubset(hist.columns):
        return pd.DataFrame()

    highs = hist["high"].astype(float).values
    lows  = hist["low"].astype(float).values
    vols  = hist["volume"].astype(float).values if "volume" in hist.columns else [1.0] * len(hist)
    n          = len(hist)
    last_close = float(hist["close"].iloc[-1])

    # ── Bước 1: tìm swing points ─────────────────────────────────────────
    swing_highs: list[tuple] = []   # (idx, price, volume)
    swing_lows:  list[tuple] = []
    for i in range(window, n - window):
        h_win = highs[i - window: i + window + 1]
        l_win = lows [i - window: i + window + 1]
        if highs[i] >= max(h_win):
            swing_highs.append((i, float(highs[i]), float(vols[i])))
        if lows[i] <= min(l_win):
            swing_lows.append((i, float(lows[i]),  float(vols[i])))

    # ── Bước 2: gom cụm và chấm điểm ────────────────────────────────────
    def _cluster(points: list) -> list[tuple]:
        """→ list[(rep_price, score, touch_count)] sorted by score desc"""
        if not points:
            return []
        pts = sorted(points, key=lambda x: x[1])
        clusters: list[list] = []
        cur: list = [pts[0]]
        for pt in pts[1:]:
            if abs(pt[1] - cur[0][1]) / (cur[0][1] + 1e-9) <= cluster_pct:
                cur.append(pt)
            else:
                clusters.append(cur)
                cur = [pt]
        clusters.append(cur)
        result = []
        for cl in clusters:
            tot_vol = sum(p[2] for p in cl) or 1.0
            rep_px  = sum(p[1] * p[2] for p in cl) / tot_vol
            score   = sum(0.5 + (p[0] / n) for p in cl)   # recency-weighted
            result.append((round(rep_px, 3), round(score, 2), len(cl)))
        return sorted(result, key=lambda x: -x[1])

    all_levels = (
        [(p, s, c, "R") for p, s, c in _cluster(swing_highs)] +
        [(p, s, c, "S") for p, s, c in _cluster(swing_lows)]
    )

    # ── Bước 3: phân loại, chọn top max_levels gần giá nhất ──────────────
    resists = sorted(
        [(p, s, c, t) for p, s, c, t in all_levels if p > last_close],
        key=lambda x: x[0]     # gần giá nhất trước
    )[:max_levels]

    supports = sorted(
        [(p, s, c, t) for p, s, c, t in all_levels if p < last_close],
        key=lambda x: -x[0]    # gần giá nhất trước
    )[:max_levels]

    rows = []
    for p, s, c, _ in reversed(resists):   # hiển thị cao → thấp
        rows.append({"Loại": "🔴 Kháng cự", "Mức giá": p, "Điểm mạnh": s, "Số lần chạm": c})
    rows.append({"Loại": "▶ Giá hiện tại", "Mức giá": round(last_close, 3),
                 "Điểm mạnh": "—", "Số lần chạm": "—"})
    for p, s, c, _ in supports:
        rows.append({"Loại": "🟢 Hỗ trợ", "Mức giá": p, "Điểm mạnh": s, "Số lần chạm": c})
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _read_outstanding_shares(ticker: str) -> float | None:
    """
    Đọc số cổ phiếu lưu hành từ block QUARTERLY của file per_ticker/{ticker}.md.
    Parse dòng '| Cổ phiếu lưu hành | <value> |'.
    """
    import re
    md_file = PER_TICKER_DIR / f"{ticker}.md"
    if not md_file.exists():
        return None
    try:
        text = md_file.read_text(encoding="utf-8")
        m = re.search(r"\|\s*Cổ phiếu lưu hành\s*\|\s*([\d,\. ]+)\s*\|", text)
        if m:
            val_str = re.sub(r"[,\. ]", "", m.group(1).strip())
            if val_str:
                return float(val_str)
    except Exception:
        pass
    return None


SNAPSHOT_MD      = BASE_DIR / "output" / "per_ticker" / "bluechip_snapshot.md"


def _last_trading_date() -> date:
    """Trả về ngày phiên giao dịch của hôm qua (pipeline chạy T+1).
    - T3–T7 (run T4–CN): trừ 1 ngày → T2–T6 ✓
    - CN  (run T+1 = CN): trừ 2 ngày → T6 ✓
    - T2  (run T+1 = T2): trừ 3 ngày → T6 tuần trước ✓
    """
    d = date.today()
    # weekday(): 0=T2, 5=T7, 6=CN
    if d.weekday() == 6:    # CN → lùi 2 ngày về T6
        d -= timedelta(days=2)
    elif d.weekday() == 0:  # T2 → lùi 3 ngày về T6 tuần trước
        d -= timedelta(days=3)
    else:                   # T3–T7 → lùi 1 ngày về phiên hôm qua
        d -= timedelta(days=1)
    return d




def fetch_price_history(stock_vci, ticker: str) -> pd.DataFrame:
    """Lịch sử giá ~90 phiên gần nhất (130 ngày lịch ≈ 90 phiên giao dịch)."""
    end   = date.today().strftime("%Y-%m-%d")
    start = (date.today() - timedelta(days=130)).strftime("%Y-%m-%d")
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
    _throttle()  # price_board không qua safe_call — phải track thủ công
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
    industry_map: dict | None = None,
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

    # ── Sector comparison ──────────────────────────────────────────────────
    if industry_map:
        sector_rows = []
        for ticker, frames in detail_map.items():
            rs = frames.get("Tóm tắt chỉ số", pd.DataFrame())
            if rs.empty:
                continue
            r = rs.iloc[0]
            def _g(keys):
                for k in keys:
                    m = [c for c in rs.columns if k.lower() in c.lower()]
                    if m: return r[m[0]]
                return "—"
            sector_rows.append({
                "Mã":       ticker,
                "Ngành":    industry_map.get(ticker, "—"),
                "P/E":      _g(["pe"]),
                "P/B":      _g(["pb"]),
                "ROE":      _g(["roe"]),
                "ROA":      _g(["roa"]),
                "EPS":      _g(["eps"]),
                "Biên LN":  _g(["net_profit_margin"]),
                "Tăng DT":  _g(["revenue_growth"]),
                "Tăng LN":  _g(["net_profit_growth"]),
            })
        if sector_rows:
            df_sector = pd.DataFrame(sector_rows).sort_values(["Ngành", "P/E"])
            lines += ["", "---", "", "## So sánh nội ngành (P/E, P/B, ROE)", "", _df_to_md(df_sector, max_rows=50)]

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


def _build_daily_block(frames: dict, ticker: str = "") -> str:
    """Trả về nội dung block DAILY (không bao gồm sentinel)."""
    ts_kv    = frames.get("Thống kê giao dịch",     pd.DataFrame())
    rs_kv    = frames.get("Tóm tắt chỉ số",         pd.DataFrame())
    tech     = frames.get("Chỉ báo kỹ thuật",        pd.DataFrame())
    news     = frames.get("Tin tức",                 pd.DataFrame())
    hist     = frames.get("Lịch sử giá",             pd.DataFrame())
    intra    = frames.get("Giao dịch trong ngày",    pd.DataFrame())
    events   = frames.get("Sự kiện",                 pd.DataFrame())
    sr       = frames.get("Vùng hỗ trợ / kháng cự", pd.DataFrame())

    # ── News: dùng news_title (VCI) hoặc title (KBS) ──────────────────────
    title_col = next((c for c in news.columns if "title" in c.lower()), None) if not news.empty else None
    date_col  = next((c for c in news.columns if "date" in c.lower() or "time" in c.lower()), None) if not news.empty else None
    if title_col and not news.empty:
        news_display = news[[c for c in [title_col, date_col, "news_source_link", "url"] if c and c in news.columns]].head(10)
    else:
        news_display = news

    # ── Volume + Turnover rate ─────────────────────────────────────────────
    vol_section_lines: list[str] = []
    if not hist.empty and "volume" in hist.columns:
        vol   = hist["volume"].astype(float)
        avg60 = vol.tail(60).mean()
        hist5 = hist.tail(5).copy()

        # Số CP lưu hành: ưu tiên frame Tổng quan (full mode), fallback parse MD
        outstanding: float | None = None
        ov_df = frames.get("Tổng quan", pd.DataFrame())
        if not ov_df.empty:
            os_raw = _ov_field(ov_df, "outstanding_share")
            try:
                outstanding = float(str(os_raw).replace(",", "").replace(".", "").strip())
            except Exception:
                pass
        if outstanding is None and ticker:
            outstanding = _read_outstanding_shares(ticker)

        vol_rows = []
        for _, row in hist5.iterrows():
            v      = float(row["volume"])
            d      = str(row.get("time", ""))[:10]
            vs_avg = f"{(v / avg60 - 1) * 100:+.1f}%" if avg60 else "—"
            tr_pct = f"{v / outstanding * 100:.3f}%" if outstanding else "—"
            vol_rows.append({"Ngày": d, "KL": int(v), "vs Avg60": vs_avg, "Turnover (%)": tr_pct})

        vol_df    = pd.DataFrame(vol_rows)
        avg60_str = f"{int(avg60):,}" if avg60 else "—"
        out_str   = f"{int(outstanding):,}" if outstanding else "N/A (chạy --mode quarterly để có dữ liệu)"
        vol_section_lines = [
            "## Khối lượng & Tỷ lệ lưu hành",
            "",
            _df_to_md(vol_df),
            "",
            f"- KL trung bình 60 phiên: **{avg60_str}**",
            f"- Số CP lưu hành: **{out_str}**",
            "",
        ]

    # ── RS vs Ngành ───────────────────────────────────────────────────────
    rs_info = frames.get("RS Ngành", {})
    if rs_info:
        s_name = rs_info.get("sector_name", "—")
        s_ch   = rs_info.get("sector_change")
        t_ch   = rs_info.get("ticker_change")
        rs_val = rs_info.get("rs_day")
        if rs_val is not None:
            if rs_val > 0:
                comment = "CP **mạnh hơn** ngành"
            elif rs_val < 0:
                comment = "CP **yếu hơn** ngành"
            else:
                comment = "CP ngang với ngành"
        else:
            comment = "—"
        rs_section_lines = [
            "## RS vs Ngành",
            "",
            "| Chỉ tiêu | Giá trị |",
            "| --- | --- |",
            f"| Ngành (KBS) | {s_name} |",
            f"| % Ngành hôm nay | {f'{s_ch:+.2f}%' if s_ch is not None else '—'} |",
            f"| % Cổ phiếu hôm nay | {f'{t_ch:+.2f}%' if t_ch is not None else '—'} |",
            f"| RS (CP − Ngành) | {f'{rs_val:+.2f}%' if rs_val is not None else '—'} |",
            f"| Nhận xét | {comment} |",
            "",
        ]
    else:
        rs_section_lines = [
            "## RS vs Ngành",
            "",
            "> ℹ️ Không lấy được dữ liệu ngành từ KBS hôm nay.",
            "",
        ]

    lines = [
        "## Thống kê giao dịch",
        "",
        _df_to_md_kv(ts_kv),
        "",
        "## Chỉ báo kỹ thuật (MA5 / MA10 / EMA20 / EMA50 / RSI14 / MACD / ATR14)",
        "",
        _df_to_md_kv(tech) if not tech.empty else "_Không đủ dữ liệu lịch sử giá_",
        "",
        "## Vùng hỗ trợ / Kháng cự",
        "",
        _df_to_md(sr) if not sr.empty else "_Không đủ dữ liệu để tính vùng S/R_",
        "",
        "## Tóm tắt chỉ số tài chính",
        "",
        _df_to_md_kv(rs_kv),
        "",
        *vol_section_lines,
        "## Tin tức gần nhất (Top 10)",
        "",
        _df_to_md(news_display, max_rows=10),
        "",
        "## Lịch sự kiện (15 gần nhất — AIS/DIV/ISS)",
        "",
        _df_to_md(events, max_rows=15),
        "",
        *rs_section_lines,
        "## Lịch sử giá (90 phiên gần nhất)",
        "",
        _df_to_md(hist.tail(90) if not hist.empty else hist, max_rows=90),
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
        daily_section     = [BEGIN_DAILY, "", _build_daily_block(frames, ticker), END_DAILY, ""]
        quarterly_section = [BEGIN_QUARTERLY, "", _build_quarterly_block(frames), END_QUARTERLY, ""]
        content = "\n".join(header + daily_section + ["---", ""] + quarterly_section)
    else:
        # ── Update in-place ──
        content = out_path.read_text(encoding="utf-8")
        if effective_mode == "daily":
            content = _replace_block(content, BEGIN_DAILY, END_DAILY, _build_daily_block(frames, ticker))
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


# ── Snapshot helpers ──────────────────────────────────────────────────────────
_SIGNAL_PRIORITY: dict[str, int] = {
    "✅ TĂNG": 0, "🔄 TRUNG TÍNH": 1, "⚠️ GIẢM": 2, "🔴 RỦI RO CAO": 3,
}
# Nhóm theo đặc tính thị trường (hardcoded; cập nhật khi thêm mã vào stocks.csv)
_SECTOR_DEFENSIVE = frozenset({"GAS", "VNM", "SAB", "PLX", "MSN"})
_SECTOR_GROWTH    = frozenset({"FPT", "MWG", "TCB", "VPB", "ACB", "MBB", "HDB", "LPB", "STB"})
_SECTOR_CYCLICAL  = frozenset({"HPG", "VHM", "VIC", "VRE", "CTG", "BID"})


def fetch_vnindex(vs) -> dict:
    """Lấy VN-Index đóng cửa hôm nay, thay đổi điểm, % và 20 phiên gần nhất."""
    try:
        end   = date.today().strftime("%Y-%m-%d")
        start = (date.today() - timedelta(days=40)).strftime("%Y-%m-%d")
        vni   = vs.stock(symbol="VNINDEX", source=SOURCE_QUOTE)
        hist  = safe_call(vni.quote.history, start=start, end=end, interval="1D")
        if hist.empty or "close" not in hist.columns or len(hist) < 2:
            return {}
        hist20 = hist.tail(20).copy()
        hist20["pct_chg"] = hist20["close"].pct_change() * 100
        close  = float(hist["close"].iloc[-1])
        prev   = float(hist["close"].iloc[-2])
        change = round(close - prev, 2)
        pct    = round(change / prev * 100, 2) if prev else 0.0
        return {"close": close, "change": change, "pct": pct, "hist20": hist20}
    except Exception as exc:
        print(f"  [WARN] VN-Index: {exc}")
        return {}


def _compute_signal(vs_ema20: str | None, vs_ema50: str | None,
                    macd_h) -> str:
    """
    ✅ TĂNG      : giá > EMA20 > EMA50, MACD hist >= 0
    🔴 RỦI RO CAO: giá < EMA20 và < EMA50
    ⚠️ GIẢM     : giá dưới EMA20 hoặc EMA50
    🔄 TRUNG TÍNH: còn lại
    """
    above20 = isinstance(vs_ema20, str) and "trên" in vs_ema20.lower()
    above50 = isinstance(vs_ema50, str) and "trên" in vs_ema50.lower()
    try:   hist_pos = float(macd_h) >= 0
    except: hist_pos = None

    if above20 and above50 and hist_pos:
        return "✅ TĂNG"
    elif not above20 and not above50:
        return "🔴 RỦI RO CAO"
    elif not above20 or not above50:
        return "⚠️ GIẢM"
    else:
        return "🔄 TRUNG TÍNH"


def _build_snapshot_row(ticker: str, frames: dict, industry_map: dict) -> dict:
    """Trích xuất các trường cần thiết cho snapshot từ frames đã fetch."""
    ts   = frames.get("Thống kê giao dịch", pd.DataFrame())
    rs   = frames.get("Tóm tắt chỉ số",     pd.DataFrame())
    tech = frames.get("Chỉ báo kỹ thuật",    pd.DataFrame())
    ev   = frames.get("Sự kiện",             pd.DataFrame())

    def _get(df: pd.DataFrame, keys: list[str]):
        if df.empty:
            return None
        r = df.iloc[0]
        for k in keys:
            m = [c for c in df.columns if k.lower() in c.lower()]
            if m:
                return r[m[0]]
        return None

    close   = _get(ts, ["match_price", "close_price", "price"])
    chg_pct = _get(ts, ["price_change_pct"])
    ff_room = _get(ts, ["foreign_room",   "foreignRoom"])
    max_h   = _get(ts, ["max_holding_ratio",     "maxHoldingRatio"])
    cur_h   = _get(ts, ["current_holding_ratio",  "currentHoldingRatio"])

    # Room NN còn lại (max - current)
    room_str = "—"
    try:
        if max_h is not None and cur_h is not None:
            room_str = f"{float(max_h) - float(cur_h):.2f}%"
        elif ff_room is not None:
            room_str = str(ff_room)
    except (ValueError, TypeError):
        pass

    def _tc(col: str):
        if tech.empty or col not in tech.columns:
            return None
        return tech.iloc[0][col]

    vs_ema20 = _tc("Giá vs EMA20")
    vs_ema50 = _tc("Giá vs EMA50")
    rsi14    = _tc("RSI(14)")
    macd_h   = _tc("MACD Histogram")

    return {
        "ticker":    ticker,
        "close":     close,
        "chg_pct":   chg_pct,
        "vs_ema20":  vs_ema20 or "—",
        "vs_ema50":  vs_ema50 or "—",
        "rsi14":     rsi14,
        "macd_h":    macd_h,
        "room_str":  room_str,
        "pe":        _get(rs, ["pe"]),
        "pb":        _get(rs, ["pb"]),
        "roe":       _get(rs, ["roe"]),
        "lnst_gr":   _get(rs, ["net_profit_growth"]),
        "industry":  industry_map.get(ticker, "—"),
        "signal":    _compute_signal(vs_ema20, vs_ema50, macd_h),
        "events_df": ev,
    }


def write_snapshot(snapshot_rows: list[dict], vnindex_data: dict, run_dt: datetime) -> None:
    """Xuất draft/output/bluechip_snapshot.md từ dữ liệu tổng hợp tất cả ticker."""
    if not snapshot_rows:
        print("  [SKIP] write_snapshot: không có dữ liệu")
        return

    ts_str = run_dt.strftime("%Y-%m-%d %H:%M")
    today  = run_dt.date()
    cutoff = today + timedelta(days=30)

    def _fmt(val, fmt: str = "{:.1f}", suffix: str = "") -> str:
        try:
            return fmt.format(float(val)) + suffix
        except (ValueError, TypeError):
            return "—"

    # ── Section 1: aggregates ─────────────────────────────────────────────
    vni_cl  = vnindex_data.get("close")
    vni_ch  = vnindex_data.get("change", 0.0)
    vni_pct = vnindex_data.get("pct",    0.0)

    sector_by_signal: dict[str, list] = {}
    for r in snapshot_rows:
        ind = r["industry"]
        if ind and ind != "—":
            sector_by_signal.setdefault(ind, []).append(r["signal"])
    worst_sector = min(sector_by_signal, key=lambda k: sum(1 for s in sector_by_signal[k] if "TĂNG" in s) - sum(1 for s in sector_by_signal[k] if "GIẢM" in s or "RỦI RO" in s)) if sector_by_signal else "—"
    best_sector  = max(sector_by_signal, key=lambda k: sum(1 for s in sector_by_signal[k] if "TĂNG" in s) - sum(1 for s in sector_by_signal[k] if "GIẢM" in s or "RỦI RO" in s)) if sector_by_signal else "—"

    # ── Build lines ───────────────────────────────────────────────────────
    lines: list[str] = [
        "# 📊 Bluechip Daily Snapshot",
        f"> 🕐 Cập nhật: {ts_str} | Nguồn: auto-generated từ per_ticker/",
        "",
        "---",
        "",
        "## 1. Tổng Quan Dòng Tiền Hôm Nay",
        "",
        "| Chỉ tiêu | Giá trị |",
        "| --- | --- |",
    ]

    if vni_cl is not None:
        sign = "+" if vni_ch >= 0 else ""
        lines.append(f"| VN-Index đóng cửa | {vni_cl:,.2f} ({sign}{vni_ch:.2f}, {sign}{vni_pct:.2f}%) |")
    else:
        lines.append("| VN-Index đóng cửa | N/A |")

    lines += [
        f"| Nhóm bị xả mạnh nhất (kỹ thuật) | {worst_sector} |",
        f"| Nhóm được mua nhiều nhất (kỹ thuật) | {best_sector} |",
        "",
        "---",
        "",
        "## 2. Bảng Scan Kỹ Thuật",
        "",
        "| Mã | Giá | %D | vs EMA20 | vs EMA50 | RSI14 | MACD Hist | Tín hiệu |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    sorted_rows = sorted(snapshot_rows, key=lambda r: _SIGNAL_PRIORITY.get(r["signal"], 2))
    for r in sorted_rows:
        pct_str = _fmt(r["chg_pct"], "{:+.2f}") + "%" if r["chg_pct"] is not None else "—"
        lines.append(
            f"| {r['ticker']} | {_fmt(r['close'], '{:,.1f}')} | {pct_str}"
            f" | {r['vs_ema20']} | {r['vs_ema50']}"
            f" | {_fmt(r['rsi14'])} | {_fmt(r['macd_h'], '{:+.3f}')}"
            f" | {r['signal']} |"
        )

    lines += [
        "",
        "**Legend:**",
        "- Tín hiệu: ✅ TĂNG | ⚠️ GIẢM | 🔄 TRUNG TÍNH | 🔴 RỦI RO CAO",
        "",
        "---",
        "",
        "## 3. Bảng Định Giá Nhanh",
        "",
        "| Mã | Ngành | P/E | P/B | ROE | LNST growth | Room NN còn |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for r in snapshot_rows:
        lines.append(
            f"| {r['ticker']} | {r['industry']}"
            f" | {_fmt(r['pe'])} | {_fmt(r['pb'])}"
            f" | {_fmt(r['roe'], suffix='%')} | {_fmt(r['lnst_gr'], suffix='%')}"
            f" | {r['room_str']} |"
        )

    # ── Section 4: Events 30 ngày tới ────────────────────────────────────
    lines += ["", "---", "", "## 4. Sự Kiện Đáng Chú Ý (90 ngày qua + 30 ngày tới)", ""]

    lookback = today - timedelta(days=90)
    ev_rows: list[dict] = []
    for r in snapshot_rows:
        ev_df = r.get("events_df")
        if not isinstance(ev_df, pd.DataFrame) or ev_df.empty:
            continue
        for _, ev_row in ev_df.iterrows():
            ev_date = None
            for dcol in ("exright_date", "record_date", "public_date"):
                if dcol not in ev_row.index:
                    continue
                raw = ev_row.get(dcol)
                if not pd.notna(raw):
                    continue
                try:
                    d = pd.to_datetime(raw).date()
                    if d.year < 2000:   # bỏ qua placeholder 1753-01-01
                        continue
                    ev_date = d
                    break
                except Exception:
                    continue
            if ev_date is None or not (lookback <= ev_date <= cutoff):
                continue
            name  = str(ev_row.get("event_list_name", ev_row.get("event_title", "—")))
            title = str(ev_row.get("event_title", ""))
            ev_rows.append({
                "Ngày":    str(ev_date),
                "Mã":      r["ticker"],
                "Sự kiện": name[:60],
                "Ghi chú": title[:80],
            })

    if ev_rows:
        lines.append(_df_to_md(pd.DataFrame(ev_rows).sort_values("Ngày", ascending=False)))
    else:
        lines.append("_Không có sự kiện trong khoảng thời gian này (dữ liệu VCI: AIS/DIV/ISS)_")

    # ── Section 5: Phân loại theo pha thị trường ─────────────────────────
    all_t     = set(r["ticker"] for r in snapshot_rows)
    buy_t     = [r["ticker"] for r in sorted_rows if r["signal"] == "✅ TĂNG"]
    neutral_t = [r["ticker"] for r in sorted_rows if r["signal"] == "🔄 TRUNG TÍNH"]
    sell_t    = [r["ticker"] for r in sorted_rows if r["signal"] == "⚠️ GIẢM"]
    risk_t    = [r["ticker"] for r in sorted_rows if r["signal"] == "🔴 RỦI RO CAO"]

    def _bl(lst) -> str:
        return ", ".join(sorted(lst)) if lst else "_Không có_"

    lines += [
        "",
        "---",
        "",
        "## 5. Phân Loại Nhanh Theo Pha Thị Trường",
        "",
        "### 🟢 Nhóm phòng thủ (tiêu dùng thiết yếu, năng lượng)",
        f"> Mã trong danh sách: **{_bl(all_t & _SECTOR_DEFENSIVE)}**",
        "",
        "### 🔵 Nhóm tăng trưởng (tech, bán lẻ, ngân hàng tăng trưởng)",
        f"> Mã trong danh sách: **{_bl(all_t & _SECTOR_GROWTH)}**",
        "",
        "### 🟡 Nhóm chu kỳ (thép, BĐS)",
        f"> Mã trong danh sách: **{_bl(all_t & _SECTOR_CYCLICAL)}**",
        "",
        "### Tín hiệu hôm nay",
        f"- ✅ TĂNG ({len(buy_t)}): {_bl(buy_t)}",
        f"- 🔄 TRUNG TÍNH ({len(neutral_t)}): {_bl(neutral_t)}",
        f"- ⚠️ GIẢM ({len(sell_t)}): {_bl(sell_t)}",
        f"- 🔴 RỦI RO CAO ({len(risk_t)}): {_bl(risk_t)}",
        "",
        "---",
        "",
        "## 6. VNINDEX 20 Phiên Gần Nhất",
        "",
    ]

    vni_hist20 = vnindex_data.get("hist20")
    if vni_hist20 is not None and not vni_hist20.empty:
        rows_vni = []
        for _, vrow in vni_hist20.iterrows():
            try:
                d = pd.to_datetime(vrow["time"]).strftime("%Y-%m-%d")
            except Exception:
                d = str(vrow.get("time", ""))
            pct_v = vrow.get("pct_chg")
            pct_str = f"{pct_v:+.2f}%" if pd.notna(pct_v) else "—"
            rows_vni.append({
                "Ngày":       d,
                "Mở":         f"{vrow['open']:,.2f}",
                "Cao":         f"{vrow['high']:,.2f}",
                "Thấp":        f"{vrow['low']:,.2f}",
                "Đóng":        f"{vrow['close']:,.2f}",
                "%Thay đổi":  pct_str,
                "KL (tỷ)": f"{vrow['volume']/1e9:.2f}",
            })
        lines.append(_df_to_md(pd.DataFrame(rows_vni)))
    else:
        lines.append("_Không có dữ liệu VNINDEX_")

    lines += [
        "",
        "---",
        "",
        "> ⚠️ File này là snapshot tổng hợp, KHÔNG thay thế `{TICKER}.md`",
        "> Dùng để lọc mã nhanh → deep-dive bằng `per_ticker/{TICKER}.md`",
    ]

    SNAPSHOT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Snapshot → {SNAPSHOT_MD}")


# ── Gatekeeping ───────────────────────────────────────────────────────────────
_MARKET_CLOSE_HOUR = 17  # 17:00 — sau giờ này không re-run cùng ngày


def _daily_is_stale(md_file: Path) -> bool:
    """
    True  → nên chạy daily (dữ liệu cũ hoặc hôm nay chưa kết phiên)
    False → bỏ qua (đã update hôm nay sau 17:00)

    Đọc dòng:  > 📅 Daily: 21/04/2026 20:18  |  ...
    """
    if not md_file.exists():
        return True
    try:
        text = md_file.read_text(encoding="utf-8")
        m = re.search(r"Daily:\s*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})", text)
        if not m:
            return True
        last_dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%d/%m/%Y %H:%M")
        if last_dt.date() < date.today():
            return True  # dữ liệu cũ → chạy
        # cùng ngày hôm nay
        return datetime.now().hour < _MARKET_CLOSE_HOUR  # trước 17h → cho chạy lại
    except Exception:
        return True  # lỗi parse → chạy cho chắc


def _snapshot_is_stale(snapshot_md: Path) -> bool:
    """
    True  → nên ghi snapshot
    False → bỏ qua (đã ghi hôm nay sau 17:00)

    Đọc dòng:  > 🕐 Cập nhật: 2026-04-21 20:18 | Nguồn: ...
    """
    if not snapshot_md.exists():
        return True
    try:
        text = snapshot_md.read_text(encoding="utf-8")
        m = re.search(r"C\u1eadp nh\u1eadt:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})", text)
        if not m:
            return True
        last_dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M")
        if last_dt.date() < date.today():
            return True
        return datetime.now().hour < _MARKET_CLOSE_HOUR
    except Exception:
        return True


# ── Core pipeline ──────────────────────────────────────────────────────────────
def run_pipeline(
    mode: str,
    force: bool = False,
    section: str | None = None,
    specific: str | None = None,
) -> None:
    """
    mode    : daily | quarterly | full
    force   : bỏ qua gatekeeping, chạy luôn kệ ngày/giờ
    section : 'ticker' → chỉ ghi per-ticker, bỏ qua snapshot
              'snapshot' → fetch data nhưng chỉ ghi snapshot, bỏ qua write_markdown_ticker
    specific: chỉ chạy 1 ticker (tự thêm vào stocks.csv nếu chưa có)
    """
    from vnstock import Vnstock

    tickers = read_tickers(INPUT_CSV)

    # ── --specific: lọc / tự thêm vào CSV ────────────────────────────────
    if specific:
        specific = specific.upper()
        if specific not in tickers:
            df_csv = pd.read_csv(INPUT_CSV)
            col = next((c for c in df_csv.columns if c.strip().lower() == "ticker"), None)
            df_csv = pd.concat([df_csv, pd.DataFrame([{col: specific}])], ignore_index=True)
            df_csv.to_csv(INPUT_CSV, index=False)
            print(f"  [AUTO-ADD] {specific} thêm vào {INPUT_CSV}")
        tickers = [specific]
    print(f"\nMode: [{mode.upper()}]  |  Mã ({len(tickers)}): {tickers}\n")

    subdir, xlsx_path, summary_md = _setup_run_paths(mode)

    vs          = Vnstock()
    detail_map: dict                    = {}
    all_sheets: dict[str, pd.DataFrame] = {}

    # ── Industry map (once per run) ────────────────────────────────────────
    industry_map: dict[str, str] = {}
    try:
        from vnstock.api.listing import Listing
        sym_ind = Listing().symbols_by_industries()
        industry_map = dict(zip(sym_ind["symbol"], sym_ind["industry_name"]))
        print(f"  Industry map loaded: {len(industry_map)} symbols")
    except Exception as exc:
        print(f"  [WARN] industry_map: {exc}")

    # ── Price board — daily + full ──
    price_board = pd.DataFrame()
    if mode in ("daily", "full"):
        print("Đang lấy bảng giá...")
        price_board = fetch_price_board(vs, tickers)
        all_sheets["Bảng Giá"] = price_board

    # ── VN-Index + snapshot containers ──────────────────────────────────
    snapshot_rows: list[dict] = []
    vnindex_data:  dict       = {}
    if mode in ("daily", "full"):
        print("Đang lấy VN-Index...")
        vnindex_data = fetch_vnindex(vs)

    # ── Sector RS cache (25 HTTP calls, một lần cho toàn pipeline) ───────
    sector_rs_cache: dict = {}
    if mode in ("daily", "full"):
        print("Building Sector RS cache from KBS...")
        sector_rs_cache = _build_sector_rs_cache()

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

        frames: dict = {}
        kbs = vs.stock(symbol=ticker, source=SOURCE_COMPANY)
        vci = vs.stock(symbol=ticker, source=SOURCE_QUOTE)

        # ── Gatekeeping: bỏ qua daily nếu đã update hôm nay sau 17h ──
        skip_daily = False
        if not is_new and not force and effective_mode in ("daily", "full"):
            if not _daily_is_stale(md_file):
                print(f"  [SKIP daily] {ticker} đã cập nhật hôm nay sau {_MARKET_CLOSE_HOUR}:00, bỏ qua.")
                skip_daily = True

        # ── Daily data ──
        if effective_mode in ("daily", "full") and not skip_daily:
            frames["Thống kê giao dịch"]   = fetch_trading_stats(vci, ticker)
            frames["Tóm tắt chỉ số"]       = fetch_ratio_summary(vci, ticker)
            frames["Tin tức"]              = fetch_news(vci, kbs, ticker)
            frames["Lịch sử giá"]          = fetch_price_history(vci, ticker)
            frames["Giao dịch trong ngày"] = fetch_intraday(vci, ticker)
            frames["Sự kiện"]              = fetch_events(vci, kbs)
            frames["Chỉ báo kỹ thuật"]        = compute_technicals(frames["Lịch sử giá"])
            frames["Vùng hỗ trợ / kháng cự"]  = compute_support_resist(frames["Lịch sử giá"])
            frames["RS Ngành"]                 = sector_rs_cache.get(ticker.upper(), {})
            snapshot_rows.append(_build_snapshot_row(ticker, frames, industry_map))

            all_sheets[f"{ticker}_TradingStats"] = frames["Thống kê giao dịch"]
            all_sheets[f"{ticker}_RatioSum"]     = frames["Tóm tắt chỉ số"]
            all_sheets[f"{ticker}_TinTuc"]       = frames["Tin tức"]
            all_sheets[f"{ticker}_LichSuGia"]    = frames["Lịch sử giá"]
            all_sheets[f"{ticker}_IntraDay"]     = frames["Giao dịch trong ngày"]
            all_sheets[f"{ticker}_SuKien"]       = frames["Sự kiện"]
            all_sheets[f"{ticker}_KyThuat"]      = frames["Chỉ báo kỹ thuật"]
            all_sheets[f"{ticker}_SuppRes"]      = frames["Vùng hỗ trợ / kháng cự"]

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

        if section != "snapshot":
            # Bỏ qua nếu daily bị skip và không có quarterly data (frames rỗng hoàn toàn)
            if not (skip_daily and effective_mode == "daily"):
                write_markdown_ticker(ticker, frames, effective_mode)
            else:
                print(f"    [SKIP write] {ticker}: không có data mới, giữ nguyên file.")
        detail_map[ticker] = frames

    # ── Output ──
    print("\nĐang xuất báo cáo...")
    write_excel(all_sheets, xlsx_path)
    if mode in ("quarterly", "full"):
        txt_path = xlsx_path.with_suffix(".txt")
        write_txt(detail_map, txt_path)
    write_markdown_summary(detail_map, price_board, summary_md, mode, industry_map)
    if mode in ("daily", "full") and snapshot_rows:
        if section == "ticker":
            print("  [SKIP snapshot] --section ticker: bỏ qua write_snapshot.")
        elif force or _snapshot_is_stale(SNAPSHOT_MD):
            write_snapshot(snapshot_rows, vnindex_data, datetime.now())
        else:
            print("  [SKIP snapshot] bluechip_snapshot đã cập nhật hôm nay sau 17:00, bỏ qua.")
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

        import shutil

        # Xóa stale rebase state nếu còn sót từ lần trước
        for stale_name in ("rebase-merge", "rebase-apply"):
            stale = Path(repo_root) / ".git" / stale_name
            if stale.exists():
                shutil.rmtree(stale, ignore_errors=True)
                print(f"  [CLEAN] Removed stale {stale_name}")

        # Đảm bảo đang ở trên branch main (tránh detached HEAD)
        head = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(repo_root), capture_output=True, text=True
        )
        if not head.stdout.strip():
            print("  [FIX] Detached HEAD — switching to main...")
            _run(["git", "checkout", "main"])

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
        # Force-push: tất cả output là auto-generated, local luôn là mới nhất
        _run(["git", "push", "--force-with-lease", "origin", "main"])
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bỏ qua gatekeeping ngày/giờ, chạy luôn kệ đã update hay chưa.",
    )
    parser.add_argument(
        "--section",
        choices=["ticker", "snapshot"],
        default=None,
        help=(
            "ticker   = chỉ ghi per-ticker .md, bỏ qua snapshot\n"
            "snapshot = chỉ ghi bluechip_snapshot.md, bỏ qua write_markdown_ticker"
        ),
    )
    parser.add_argument(
        "--specific",
        default=None,
        metavar="TICKER",
        help="Chỉ chạy 1 mã cụ thể (VD: --specific BID). Tự thêm vào stocks.csv nếu chưa có.",
    )
    args = parser.parse_args()
    run_pipeline(args.mode, force=args.force, section=args.section, specific=args.specific)


if __name__ == "__main__":
    main()
