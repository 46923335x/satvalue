"""Local SatValue server with a server-side Alpaca market-data proxy."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone
from html import unescape
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from math import sqrt
from pathlib import Path
from statistics import stdev
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
ALPACA_DATA_URL = "https://data.alpaca.markets"
COIN_METRICS_DATA_URL = "https://community-api.coinmetrics.io/v4"
COINBASE_EXCHANGE_URL = "https://api.exchange.coinbase.com"
CACHE_SECONDS = 300
FUND_CACHE_SECONDS = 6 * 60 * 60
RANKING_CACHE_SECONDS = 15 * 60
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
_cache: dict[str, tuple[float, dict]] = {}
_btc_cache: tuple[float, date, date, list[dict]] | None = None
_fund_cache: dict[str, tuple[float, dict]] = {}
_ranking_cache: dict[str, tuple[float, dict]] = {}
_portfolio_cache: dict[str, tuple[float, dict]] = {}
_ticker_cache: tuple[float, dict] | None = None
_provider_state: dict[str, dict] = {}
_analytics: dict[str, int] = {}
_cache_lock = threading.Lock()

STATE_STREET_BASE = "https://www.ssga.com/us/en/individual/etfs"
SECTORS = [
    {"key": "communication-services", "name": "Communication Services", "symbol": "XLC", "inceptionDate": "2018-06-18", "description": "Diversified and wireless telecommunications, media, entertainment, and interactive media and services.", "slug": "state-street-communication-services-select-sector-spdr-etf-xlc"},
    {"key": "consumer-discretionary", "name": "Consumer Discretionary", "symbol": "XLY", "inceptionDate": "1998-12-16", "description": "Retail, automobiles, consumer durables, hotels, restaurants, leisure, and other discretionary businesses.", "slug": "state-street-consumer-discretionary-select-sector-spdr-etf-xly"},
    {"key": "consumer-staples", "name": "Consumer Staples", "symbol": "XLP", "inceptionDate": "1998-12-16", "description": "Food, beverages, household products, personal products, and other essential consumer businesses.", "slug": "state-street-consumer-staples-select-sector-spdr-etf-xlp"},
    {"key": "energy", "name": "Energy", "symbol": "XLE", "inceptionDate": "1998-12-16", "description": "Oil, gas, consumable fuels, and energy equipment and services companies.", "slug": "state-street-energy-select-sector-spdr-etf-xle"},
    {"key": "financials", "name": "Financials", "symbol": "XLF", "inceptionDate": "1998-12-16", "description": "Banks, insurance, capital markets, consumer finance, and diversified financial services.", "slug": "state-street-financial-select-sector-spdr-etf-xlf"},
    {"key": "health-care", "name": "Health Care", "symbol": "XLV", "inceptionDate": "1998-12-16", "description": "Pharmaceuticals, biotechnology, equipment, supplies, providers, and health-care services.", "slug": "state-street-health-care-select-sector-spdr-etf-xlv"},
    {"key": "industrials", "name": "Industrials", "symbol": "XLI", "inceptionDate": "1998-12-16", "description": "Capital goods, transportation, and commercial and professional services companies.", "slug": "state-street-industrial-select-sector-spdr-etf-xli"},
    {"key": "materials", "name": "Materials", "symbol": "XLB", "inceptionDate": "1998-12-16", "description": "Chemicals, metals, mining, construction materials, containers, packaging, and paper products.", "slug": "state-street-materials-select-sector-spdr-etf-xlb"},
    {"key": "real-estate", "name": "Real Estate", "symbol": "XLRE", "inceptionDate": "2015-10-07", "description": "Equity real estate investment trusts and real estate management and development companies.", "slug": "state-street-real-estate-select-sector-spdr-etf-xlre"},
    {"key": "technology", "name": "Technology", "symbol": "XLK", "inceptionDate": "1998-12-16", "description": "Software, hardware, semiconductors, and information-technology services companies.", "slug": "state-street-technology-select-sector-spdr-etf-xlk"},
    {"key": "utilities", "name": "Utilities", "symbol": "XLU", "inceptionDate": "1998-12-16", "description": "Electric, gas, water, independent power, and renewable electricity providers.", "slug": "state-street-utilities-select-sector-spdr-etf-xlu"},
]
for _sector in SECTORS:
    _sector["issuerUrl"] = f"{STATE_STREET_BASE}/{_sector['slug']}"
    _sector["expenseRatio"] = 0.08
    _sector["benchmark"] = f"{_sector['name']} Select Sector Index"

ASSET_CLASSES = [
    {"key": "commodities", "name": "Commodities", "symbol": "DBC", "issuer": "Invesco", "issuerUrl": "https://www.invesco.com/us/financial-products/etfs/product-detail?audienceType=Investor&ticker=DBC", "inceptionDate": "2006-02-03"},
    {"key": "international-developed", "name": "Intl Developed Markets", "symbol": "VEA", "issuer": "Vanguard", "issuerUrl": "https://investor.vanguard.com/investment-products/etfs/profile/vea", "inceptionDate": "2007-07-20"},
    {"key": "real-estate", "name": "REIT", "symbol": "VNQ", "issuer": "Vanguard", "issuerUrl": "https://investor.vanguard.com/investment-products/etfs/profile/vnq", "inceptionDate": "2004-09-23"},
    {"key": "gold", "name": "Gold", "symbol": "GLD", "issuer": "State Street", "issuerUrl": "https://www.spdrgoldshares.com/usa/", "inceptionDate": "2004-11-18"},
    {"key": "emerging-markets", "name": "Emerging Markets", "symbol": "VWO", "issuer": "Vanguard", "issuerUrl": "https://investor.vanguard.com/investment-products/etfs/profile/vwo", "inceptionDate": "2005-03-04"},
    {"key": "us-equities", "name": "US Stock Market", "symbol": "VTI", "issuer": "Vanguard", "issuerUrl": "https://investor.vanguard.com/investment-products/etfs/profile/vti", "inceptionDate": "2001-05-24"},
    {"key": "short-treasuries", "name": "Short Treasuries", "symbol": "SHY", "issuer": "iShares", "issuerUrl": "https://www.ishares.com/us/products/239452/ishares-1-3-year-treasury-bond-etf", "inceptionDate": "2002-07-22"},
    {"key": "total-bond-market", "name": "Total Bond Market", "symbol": "BND", "issuer": "Vanguard", "issuerUrl": "https://investor.vanguard.com/investment-products/etfs/profile/bnd", "inceptionDate": "2007-04-03"},
    {"key": "treasuries", "name": "Intermediate Treasuries", "symbol": "IEF", "issuer": "iShares", "issuerUrl": "https://www.ishares.com/us/products/239456/ishares-710-year-treasury-bond-etf", "inceptionDate": "2002-07-22"},
    {"key": "long-treasuries", "name": "Long Treasuries", "symbol": "TLT", "issuer": "iShares", "issuerUrl": "https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf", "inceptionDate": "2002-07-22"},
    {"key": "global-bonds", "name": "Global Bonds", "symbol": "BNDX", "issuer": "Vanguard", "issuerUrl": "https://investor.vanguard.com/investment-products/etfs/profile/bndx", "inceptionDate": "2013-05-31"},
]

COUNTRIES = [
    {"key": "australia", "name": "Australia", "symbol": "EWA", "iso3": "AUS", "lat": -25.3, "lon": 133.8, "inceptionDate": "1996-03-12"},
    {"key": "brazil", "name": "Brazil", "symbol": "EWZ", "iso3": "BRA", "lat": -14.2, "lon": -51.9, "inceptionDate": "2000-07-10"},
    {"key": "canada", "name": "Canada", "symbol": "EWC", "iso3": "CAN", "lat": 56.1, "lon": -106.3, "inceptionDate": "1996-03-12"},
    {"key": "china", "name": "China", "symbol": "MCHI", "iso3": "CHN", "lat": 35.8, "lon": 104.1, "inceptionDate": "2011-03-29"},
    {"key": "france", "name": "France", "symbol": "EWQ", "iso3": "FRA", "lat": 46.2, "lon": 2.2, "inceptionDate": "1996-03-12"},
    {"key": "germany", "name": "Germany", "symbol": "EWG", "iso3": "DEU", "lat": 51.2, "lon": 10.4, "inceptionDate": "1996-03-12"},
    {"key": "italy", "name": "Italy", "symbol": "EWI", "iso3": "ITA", "lat": 42.8, "lon": 12.5, "inceptionDate": "1996-03-12"},
    {"key": "japan", "name": "Japan", "symbol": "EWJ", "iso3": "JPN", "lat": 36.2, "lon": 138.2, "inceptionDate": "1996-03-12"},
    {"key": "south-korea", "name": "South Korea", "symbol": "EWY", "iso3": "KOR", "lat": 36.5, "lon": 127.9, "inceptionDate": "2000-05-09"},
    {"key": "switzerland", "name": "Switzerland", "symbol": "EWL", "iso3": "CHE", "lat": 46.8, "lon": 8.2, "inceptionDate": "1996-03-12"},
    {"key": "united-kingdom", "name": "United Kingdom", "symbol": "EWU", "iso3": "GBR", "lat": 55.3, "lon": -3.4, "inceptionDate": "1996-03-12"},
    {"key": "united-states", "name": "United States", "symbol": "SPY", "iso3": "USA", "lat": 39.8, "lon": -98.6, "inceptionDate": "1993-01-22"},
]
ISHARES_COUNTRY_PRODUCT_IDS = {
    "EWA": "239607", "EWZ": "239612", "EWC": "239615", "MCHI": "239619",
    "EWQ": "239648", "EWG": "239650", "EWI": "239664", "EWJ": "239665",
    "EWY": "239681", "EWL": "239685", "EWU": "239690",
}
for _country in COUNTRIES:
    _country["issuer"] = "State Street" if _country["symbol"] == "SPY" else "iShares"
    _country["issuerUrl"] = (
        "https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy"
        if _country["symbol"] == "SPY"
        else f"https://www.ishares.com/us/products/{ISHARES_COUNTRY_PRODUCT_IDS[_country['symbol']]}"
    )

REGISTRY_BY_SYMBOL = {item["symbol"]: item for item in [*SECTORS, *ASSET_CLASSES, *COUNTRIES]}
REGISTRY_VERSION = "2026.08.02.2"

MARKET_TICKER = [
    {"label": "S&P 500", "symbol": "SPY"},
    {"label": "Nasdaq 100", "symbol": "QQQ"},
    {"label": "Gold", "symbol": "GLD"},
    {"label": "Oil", "symbol": "USO"},
    {"label": "US Dollar", "symbol": "UUP"},
    {"label": "Communication Services", "symbol": "XLC"},
]

STATE_STREET_XLC_URL = next(item["issuerUrl"] for item in SECTORS if item["symbol"] == "XLC")

XLC_FALLBACK = {
    "symbol": "XLC",
    "asOf": "2026-07-30",
    "source": "State Street Investment Management",
    "sourceUrl": STATE_STREET_XLC_URL,
    "industryAllocations": [
        {"name": "Interactive Media & Services", "weight": 35.20},
        {"name": "Entertainment", "weight": 29.30},
        {"name": "Media", "weight": 16.85},
        {"name": "Diversified Telecommunication Services", "weight": 14.11},
        {"name": "Wireless Telecommunication Services", "weight": 4.55},
    ],
    "topHoldings": [
        {"name": "Meta Platforms Class A", "weight": 16.28},
        {"name": "Alphabet Class A", "weight": 10.44},
        {"name": "Alphabet Class C", "weight": 8.42},
        {"name": "AT&T", "weight": 4.85},
        {"name": "Verizon Communications", "weight": 4.77},
    ],
}


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()


class MarketDataError(RuntimeError):
    pass


class PortfolioValidationError(MarketDataError):
    pass


def read_request_body(headers, stream, max_bytes: int) -> bytes:
    """Read a bounded HTTP request body from fixed-length or chunked requests."""
    length_header = headers.get("Content-Length")
    if length_header:
        length = int(length_header)
        if not 0 < length <= max_bytes:
            raise MarketDataError("Request body is empty or too large.")
        body = stream.read(length)
        if len(body) != length:
            raise MarketDataError("Request body is incomplete.")
        return body

    transfer_encoding = str(headers.get("Transfer-Encoding", "")).lower()
    if "chunked" not in transfer_encoding:
        raise MarketDataError("Request body is empty or too large.")

    body = bytearray()
    while True:
        size_line = stream.readline(128)
        if not size_line:
            raise MarketDataError("Request body is incomplete.")
        try:
            chunk_size = int(size_line.split(b";", 1)[0].strip(), 16)
        except ValueError as exc:
            raise MarketDataError("Request body is invalid.") from exc
        if chunk_size == 0:
            while True:
                trailer = stream.readline(8192)
                if trailer in {b"\r\n", b"\n", b""}:
                    break
            break
        if chunk_size < 0 or len(body) + chunk_size > max_bytes:
            raise MarketDataError("Request body is empty or too large.")
        chunk = stream.read(chunk_size)
        if len(chunk) != chunk_size or stream.read(2) != b"\r\n":
            raise MarketDataError("Request body is incomplete.")
        body.extend(chunk)

    if not body:
        raise MarketDataError("Request body is empty or too large.")
    return bytes(body)


def alpaca_headers() -> dict[str, str]:
    key_id = os.environ.get("ALPACA_API_KEY_ID")
    secret_key = os.environ.get("ALPACA_API_SECRET_KEY")
    if not key_id or not secret_key:
        raise MarketDataError("Alpaca credentials are not configured.")
    return {
        "Accept": "application/json",
        "APCA-API-KEY-ID": key_id,
        "APCA-API-SECRET-KEY": secret_key,
        "User-Agent": "SatValue-local/1.0",
    }


def alpaca_pages(path: str, params: dict[str, str], symbol: str) -> list[dict]:
    bars: list[dict] = []
    page_token: str | None = None

    while True:
        query = dict(params)
        if page_token:
            query["page_token"] = page_token
        url = f"{ALPACA_DATA_URL}{path}?{urlencode(query)}"
        request = Request(url, headers=alpaca_headers())
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("message")
            except Exception:
                detail = None
            raise MarketDataError(detail or f"Alpaca returned HTTP {exc.code}.") from exc
        except URLError as exc:
            raise MarketDataError("Alpaca market data is temporarily unreachable.") from exc

        payload_bars = payload.get("bars") or {}
        bars.extend(payload_bars.get(symbol) or [])
        page_token = payload.get("next_page_token")
        if not page_token:
            break

    return bars


def alpaca_multi_pages(path: str, params: dict[str, str], symbols: list[str]) -> dict[str, list[dict]]:
    bars = {symbol: [] for symbol in symbols}
    page_token: str | None = None
    while True:
        query = dict(params)
        if page_token:
            query["page_token"] = page_token
        request = Request(f"{ALPACA_DATA_URL}{path}?{urlencode(query)}", headers=alpaca_headers())
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise MarketDataError(f"Alpaca returned HTTP {exc.code} while loading rankings.") from exc
        except URLError as exc:
            raise MarketDataError("Alpaca ranking data is temporarily unreachable.") from exc
        payload_bars = payload.get("bars") or {}
        for symbol in symbols:
            bars[symbol].extend(payload_bars.get(symbol) or [])
        page_token = payload.get("next_page_token")
        if not page_token:
            return bars


def coin_metrics_btc_prices(start: date, end: date) -> list[dict]:
    params = {
        "assets": "btc",
        "metrics": "PriceUSD",
        "frequency": "1d",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "page_size": "10000",
        "paging_from": "start",
    }
    url: str | None = f"{COIN_METRICS_DATA_URL}/timeseries/asset-metrics?{urlencode(params)}"
    bars: list[dict] = []

    while url:
        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "SatValue-local/1.0"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise MarketDataError(f"Coin Metrics returned HTTP {exc.code}.") from exc
        except URLError as exc:
            raise MarketDataError("Coin Metrics Bitcoin data is temporarily unreachable.") from exc

        for point in payload.get("data") or []:
            try:
                price = float(point["PriceUSD"])
            except (KeyError, TypeError, ValueError):
                continue
            if price <= 0:
                continue
            bars.append(
                {
                    "t": str(point["time"]),
                    "o": price,
                    "h": price,
                    "l": price,
                    "c": price,
                }
            )
        url = payload.get("next_page_url")

    return bars


def coinbase_btc_candles(start: date, end: date) -> list[dict]:
    global _btc_cache
    now = time.monotonic()
    with _cache_lock:
        if (
            _btc_cache
            and now - _btc_cache[0] < CACHE_SECONDS
            and _btc_cache[1] <= start
            and _btc_cache[2] >= end
        ):
            return _btc_cache[3]

    candles_by_date: dict[str, dict] = {}
    window_start = start

    while window_start <= end:
        window_end = min(end, window_start + timedelta(days=299))
        params = {
            "granularity": "86400",
            "start": f"{window_start.isoformat()}T00:00:00Z",
            "end": f"{window_end.isoformat()}T23:59:59Z",
        }
        url = f"{COINBASE_EXCHANGE_URL}/products/BTC-USD/candles?{urlencode(params)}"
        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "SatValue-local/1.0"},
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise MarketDataError(f"Coinbase returned HTTP {exc.code}.") from exc
        except URLError as exc:
            raise MarketDataError("Coinbase Bitcoin data is temporarily unreachable.") from exc

        if not isinstance(payload, list):
            raise MarketDataError("Coinbase returned an unexpected candle response.")
        for candle in payload:
            if not isinstance(candle, list) or len(candle) < 5:
                continue
            try:
                timestamp, low, high, open_price, close = candle[:5]
                candle_date = datetime.fromtimestamp(float(timestamp), timezone.utc).date().isoformat()
                parsed = {
                    "t": f"{candle_date}T00:00:00Z",
                    "o": float(open_price),
                    "h": float(high),
                    "l": float(low),
                    "c": float(close),
                }
            except (TypeError, ValueError, OSError):
                continue
            if min(parsed["o"], parsed["h"], parsed["l"], parsed["c"]) <= 0:
                continue
            candles_by_date[candle_date] = parsed

        window_start = window_end + timedelta(days=1)

    bars = [candles_by_date[key] for key in sorted(candles_by_date)]
    if not bars:
        raise MarketDataError("Coinbase returned no BTC/USD candles.")
    with _cache_lock:
        _btc_cache = (now, start, end, bars)
    return bars


def bar_date(bar: dict) -> str:
    return str(bar["t"])[:10]


def build_ratio_series(stock_bars: list[dict], btc_bars: list[dict]) -> list[dict]:
    btc_by_date = {bar_date(bar): bar for bar in btc_bars}
    result: list[dict] = []

    for stock in stock_bars:
        day = bar_date(stock)
        btc = btc_by_date.get(day)
        if not btc:
            continue
        try:
            stock_open = float(stock["o"])
            stock_high = float(stock["h"])
            stock_low = float(stock["l"])
            stock_close = float(stock["c"])
            btc_open = float(btc["o"])
            btc_high = float(btc["h"])
            btc_low = float(btc["l"])
            btc_close = float(btc["c"])
        except (KeyError, TypeError, ValueError):
            continue
        if min(stock_open, stock_high, stock_low, stock_close, btc_open, btc_high, btc_low, btc_close) <= 0:
            continue

        result.append(
            {
                "time": day,
                "open": stock_open / btc_open,
                "high": stock_high / btc_low,
                "low": stock_low / btc_high,
                "close": stock_close / btc_close,
            }
        )

    return result


def shift_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    month_lengths = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return date(year, month, min(value.day, month_lengths[month - 1]))


def return_for_target(series: list[dict], target: date) -> float | None:
    if not series:
        return None
    first_date = date.fromisoformat(series[0]["time"])
    if first_date > target:
        return None
    base = None
    for point in series:
        point_date = date.fromisoformat(point["time"])
        if point_date <= target:
            base = point
        else:
            break
    if not base or base["close"] <= 0:
        return None
    return ((series[-1]["close"] / base["close"]) - 1) * 100


def trailing_returns(series: list[dict]) -> dict[str, float | None]:
    if not series:
        return {}
    latest = date.fromisoformat(series[-1]["time"])
    targets = {
        "YTD": date(latest.year - 1, 12, 31),
        "1-Month": shift_months(latest, 1),
        "1-Year": shift_months(latest, 12),
        "3-Year": shift_months(latest, 36),
        "5-Year": shift_months(latest, 60),
        "10-Year": shift_months(latest, 120),
    }
    return {label: return_for_target(series, target) for label, target in targets.items()}


def research_metrics(series: list[dict]) -> dict:
    if len(series) < 2:
        return {"cagr": None, "annualizedVolatility": None, "maxDrawdown": None, "currentDrawdown": None}
    start_date = date.fromisoformat(series[0]["time"])
    end_date = date.fromisoformat(series[-1]["time"])
    elapsed_years = max((end_date - start_date).days / 365.2425, 1 / 365.2425)
    start_close = float(series[0]["close"])
    end_close = float(series[-1]["close"])
    cagr = ((end_close / start_close) ** (1 / elapsed_years) - 1) * 100 if start_close > 0 else None
    returns = [
        float(series[index]["close"]) / float(series[index - 1]["close"]) - 1
        for index in range(1, len(series))
        if float(series[index - 1]["close"]) > 0
    ]
    volatility = stdev(returns) * sqrt(252) * 100 if len(returns) > 1 else None
    peak = float(series[0]["close"])
    drawdowns = []
    for point in series:
        close = float(point["close"])
        peak = max(peak, close)
        drawdowns.append({"time": point["time"], "value": (close / peak - 1) * 100})
    return {
        "cagr": cagr,
        "annualizedVolatility": volatility,
        "maxDrawdown": min(point["value"] for point in drawdowns),
        "currentDrawdown": drawdowns[-1]["value"],
        "drawdowns": drawdowns,
    }


def calendar_returns(series: list[dict]) -> list[dict]:
    year_end: dict[int, dict] = {}
    for point in series:
        year_end[date.fromisoformat(point["time"]).year] = point
    years = sorted(year_end)
    rows = []
    for index in range(1, len(years)):
        previous = float(year_end[years[index - 1]]["close"])
        current = float(year_end[years[index]]["close"])
        rows.append({"year": years[index], "return": ((current / previous) - 1) * 100 if previous > 0 else None})
    return list(reversed(rows))


def rolling_returns(series: list[dict], months: int = 12) -> list[dict]:
    """Return rolling cumulative returns using the last observation on or before each target."""
    if not series:
        return []
    rows: list[dict] = []
    base_index = 0
    first_date = date.fromisoformat(series[0]["time"])
    for point in series:
        point_date = date.fromisoformat(point["time"])
        target = shift_months(point_date, months)
        if target < first_date:
            continue
        while base_index + 1 < len(series) and date.fromisoformat(series[base_index + 1]["time"]) <= target:
            base_index += 1
        base = float(series[base_index]["close"])
        current = float(point["close"])
        if base > 0:
            rows.append({"time": point["time"], "value": (current / base - 1) * 100})
    return rows


def rebalance_period(day: date, frequency: str) -> tuple[int, int] | tuple[int]:
    if frequency == "monthly":
        return day.year, day.month
    if frequency == "quarterly":
        return day.year, (day.month - 1) // 3
    return (day.year,)


def build_portfolio_values(
    dates: list[str],
    closes_by_symbol: dict[str, dict[str, float]],
    btc_closes: dict[str, float],
    benchmark_closes_by_symbol: dict[str, dict[str, float]],
    weights: dict[str, float],
    rebalancing: str,
    initial_btc_balance: float = 10.0,
) -> list[dict]:
    """Build adjusted-close total-return proxy values for a weighted portfolio and benchmarks."""
    if len(dates) < 2:
        raise MarketDataError("At least two shared daily observations are required for a backtest.")
    first = dates[0]
    initial_value = initial_btc_balance * btc_closes[first]
    shares = {
        symbol: initial_value * weight / closes_by_symbol[symbol][first]
        for symbol, weight in weights.items()
    }
    btc_units = initial_value / btc_closes[first]
    benchmark_shares = {
        symbol: initial_value / closes[first]
        for symbol, closes in benchmark_closes_by_symbol.items()
    }
    initial_btc_value = initial_btc_balance
    prior_period = rebalance_period(date.fromisoformat(first), rebalancing)
    rows: list[dict] = []

    for day_text in dates:
        day = date.fromisoformat(day_text)
        current_period = rebalance_period(day, rebalancing)
        portfolio_usd = sum(shares[symbol] * closes_by_symbol[symbol][day_text] for symbol in weights)
        if rebalancing != "none" and current_period != prior_period:
            shares = {
                symbol: portfolio_usd * weight / closes_by_symbol[symbol][day_text]
                for symbol, weight in weights.items()
            }
            prior_period = current_period
        btc_price = btc_closes[day_text]
        portfolio_btc = portfolio_usd / btc_price
        benchmark_values = {
            symbol: benchmark_shares[symbol] * closes[day_text]
            for symbol, closes in benchmark_closes_by_symbol.items()
        }
        rows.append({
            "time": day_text,
            "portfolioUsd": portfolio_usd,
            "portfolioBtc": portfolio_btc,
            "portfolioBtcIndex": 10000.0 * portfolio_btc / initial_btc_value,
            "bitcoinBtc": initial_btc_value,
            "btcUsd": btc_units * btc_price,
            "benchmarksUsd": benchmark_values,
            "benchmarksBtc": {symbol: value / btc_price for symbol, value in benchmark_values.items()},
            "benchmarksBtcIndex": {symbol: 10000.0 * (value / btc_price) / initial_btc_value for symbol, value in benchmark_values.items()},
        })
    return rows


def validate_portfolio_request(payload: dict) -> tuple[dict[str, float], str, date | None, list[str]]:
    holdings = payload.get("holdings")
    if not isinstance(holdings, list) or not 2 <= len(holdings) <= 20:
        raise PortfolioValidationError("Enter between 2 and 20 portfolio holdings.")
    weights: dict[str, float] = {}
    for holding in holdings:
        if not isinstance(holding, dict):
            raise PortfolioValidationError("Each holding must include a ticker and weight.")
        symbol = str(holding.get("symbol", "")).strip().upper()
        if not SYMBOL_PATTERN.fullmatch(symbol):
            raise PortfolioValidationError(f"Enter a valid US stock or ETF symbol: {symbol or 'blank'}.")
        if symbol in weights:
            raise PortfolioValidationError(f"Remove the duplicate holding {symbol}.")
        try:
            percent = float(holding.get("weight"))
        except (TypeError, ValueError):
            raise PortfolioValidationError(f"Enter a numeric weight for {symbol}.")
        if not 0 < percent <= 100:
            raise PortfolioValidationError(f"Weight for {symbol} must be greater than 0% and no more than 100%.")
        weights[symbol] = percent / 100
    if abs(sum(weights.values()) - 1) > 0.0001:
        raise PortfolioValidationError("Portfolio weights must total 100%.")

    raw_benchmarks = payload.get("benchmarks", ["SPY"])
    if isinstance(raw_benchmarks, str):
        raw_benchmarks = raw_benchmarks.split(",")
    if not isinstance(raw_benchmarks, list):
        raise PortfolioValidationError("Enter benchmark tickers separated by commas.")
    benchmarks = [str(symbol).strip().upper() for symbol in raw_benchmarks if str(symbol).strip()]
    if not 1 <= len(benchmarks) <= 5:
        raise PortfolioValidationError("Enter between one and five benchmark tickers.")
    if len(set(benchmarks)) != len(benchmarks):
        raise PortfolioValidationError("Remove duplicate benchmark tickers.")
    for symbol in benchmarks:
        if not SYMBOL_PATTERN.fullmatch(symbol):
            raise PortfolioValidationError(f"Enter a valid US stock or ETF benchmark ticker: {symbol}.")
        if symbol in {"BTC", "BTCUSD", "BTC/USD"}:
            raise PortfolioValidationError("Bitcoin is the numeraire and cannot also be entered as a benchmark.")

    rebalancing = str(payload.get("rebalancing", "monthly")).lower()
    if rebalancing not in {"monthly", "quarterly", "annual", "none"}:
        raise PortfolioValidationError("Choose monthly, quarterly, annual, or no rebalancing.")

    requested_start = None
    start_text = str(payload.get("startDate") or "").strip()
    if start_text:
        try:
            requested_start = date.fromisoformat(start_text)
        except ValueError as exc:
            raise PortfolioValidationError("Enter a valid portfolio start date.") from exc
        if requested_start < date(2015, 7, 20):
            raise PortfolioValidationError("Portfolio backtests cannot begin before July 20, 2015, the configured Bitcoin data start.")
        if requested_start >= datetime.now(timezone.utc).date():
            raise PortfolioValidationError("Portfolio start date must be before today.")
    return weights, rebalancing, requested_start, benchmarks


def fetch_portfolio_payload(payload: dict) -> dict:
    weights, rebalancing, requested_start, benchmarks = validate_portfolio_request(payload)
    now = datetime.now(timezone.utc)
    last_complete_date = now.date() - timedelta(days=1)
    earliest_supported = date(2015, 7, 20)
    fetch_start = max(earliest_supported, requested_start or earliest_supported)
    symbols = list(weights)
    market_symbols = list(dict.fromkeys([*symbols, *benchmarks]))
    params = {
        "symbols": ",".join(market_symbols),
        "timeframe": "1Day",
        "start": fetch_start.isoformat(),
        "end": (now - timedelta(minutes=20)).isoformat().replace("+00:00", "Z"),
        "limit": "10000",
        "sort": "asc",
        "adjustment": "all",
        "feed": "sip",
    }
    stock_sets = alpaca_multi_pages("/v2/stocks/bars", params, market_symbols)
    close_sets: dict[str, dict[str, float]] = {}
    for symbol in market_symbols:
        close_sets[symbol] = {
            bar_date(bar): float(bar["c"])
            for bar in stock_sets.get(symbol, [])
            if date.fromisoformat(bar_date(bar)) <= last_complete_date and float(bar.get("c", 0)) > 0
        }
        if not close_sets[symbol]:
            raise MarketDataError(f"No adjusted Alpaca history was returned for {symbol}.")
    try:
        btc_bars = coinbase_btc_candles(fetch_start, last_complete_date)
        btc_source = "Coinbase Exchange BTC/USD"
    except MarketDataError:
        btc_bars = coin_metrics_btc_prices(fetch_start, last_complete_date)
        btc_source = "Coin Metrics PriceUSD"
    btc_closes = {bar_date(bar): float(bar["c"]) for bar in btc_bars if float(bar.get("c", 0)) > 0}
    if not btc_closes:
        raise MarketDataError("No Bitcoin benchmark history was returned.")

    common_dates = set(btc_closes)
    for symbol in market_symbols:
        common_dates &= set(close_sets[symbol])
    dates = sorted(day for day in common_dates if requested_start is None or date.fromisoformat(day) >= requested_start)
    if len(dates) < 2:
        raise MarketDataError("The holdings do not have enough shared history for this backtest.")

    rows = build_portfolio_values(
        dates,
        {symbol: close_sets[symbol] for symbol in symbols},
        btc_closes,
        {symbol: close_sets[symbol] for symbol in benchmarks},
        weights,
        rebalancing,
    )
    portfolio_btc_series = [{"time": row["time"], "close": row["portfolioBtcIndex"]} for row in rows]
    benchmark_btc_series = {
        symbol: [{"time": row["time"], "close": row["benchmarksBtcIndex"][symbol]} for row in rows]
        for symbol in benchmarks
    }
    def summarized_metrics(values: list[dict]) -> dict:
        calculated = research_metrics(values)
        return {metric: value for metric, value in calculated.items() if metric != "drawdowns"}
    metrics = {
        "portfolioVsBtc": summarized_metrics(portfolio_btc_series),
        "benchmarks": {symbol: summarized_metrics(values) for symbol, values in benchmark_btc_series.items()},
    }
    effective_start = dates[0]
    warnings = []
    if requested_start and effective_start > requested_start.isoformat():
        warnings.append(f"The effective start moved to {effective_start}, the first shared completed observation for every holding and benchmark.")
    available_starts = {symbol: min(close_sets[symbol]) for symbol in market_symbols}
    return {
        "holdings": [{"symbol": symbol, "weight": weight * 100, "availableStart": available_starts[symbol]} for symbol, weight in weights.items()],
        "benchmarks": [{"symbol": symbol, "availableStart": available_starts[symbol]} for symbol in benchmarks],
        "rebalancing": rebalancing,
        "requestedStart": requested_start.isoformat() if requested_start else None,
        "effectiveStart": effective_start,
        "availableEnd": dates[-1],
        "asOf": dates[-1],
        "source": "Alpaca SIP adjusted equities + " + ("Coinbase Exchange Bitcoin daily data" if "Coinbase" in btc_source else "Coin Metrics Bitcoin daily data"),
        "series": [{
            "time": row["time"],
            "portfolioBtc": row["portfolioBtc"],
            "benchmarksBtc": row["benchmarksBtc"],
        } for row in rows],
        "metrics": metrics,
        "trailingReturns": {
            "portfolioVsBtc": trailing_returns(portfolio_btc_series),
            "benchmarks": {symbol: trailing_returns(values) for symbol, values in benchmark_btc_series.items()},
        },
        "rollingReturns": rolling_returns(portfolio_btc_series, 12),
        "calendarReturns": {
            "portfolioVsBtc": calendar_returns(portfolio_btc_series),
            "benchmarks": {symbol: calendar_returns(values) for symbol, values in benchmark_btc_series.items()},
        },
        "warnings": warnings,
        "methodology": "The portfolio and each selected benchmark begin with a 10 BTC balance. Adjusted daily equity closing prices are treated as total-return proxies for dividends and splits, then divided by the aligned Bitcoin closing price. Returns, volatility, and drawdowns are calculated only from those BTC-denominated series. The portfolio rebalances at the first shared trading close of each selected period and excludes dates without a completed observation for every holding, selected benchmark, and Bitcoin. Delisted symbols are supported only when Alpaca returns adjusted history.",
        "stale": (last_complete_date - date.fromisoformat(dates[-1])).days > 4,
        "cacheTtlSeconds": CACHE_SECONDS,
    }


def cached_portfolio_payload(payload: dict) -> dict:
    cache_key = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    now = time.monotonic()
    with _cache_lock:
        cached = _portfolio_cache.get(cache_key)
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]
    result = fetch_portfolio_payload(payload)
    with _cache_lock:
        _portfolio_cache[cache_key] = (now, result)
    return result


def security_metadata(symbol: str) -> dict:
    if symbol == "BTCUSD":
        return {"name": "Bitcoin", "proxy": "BTC/USD", "dataStartDate": "2015-07-20", "issuer": "Coinbase Exchange", "issuerUrl": "https://exchange.coinbase.com/trade/BTC-USD"}
    if symbol == "SPY":
        return {"name": "S&P 500", "proxy": "SPY", "inceptionDate": "1993-01-22", "issuer": "State Street", "issuerUrl": "https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy"}
    registered = REGISTRY_BY_SYMBOL.get(symbol)
    if registered:
        return {
            "name": registered["name"],
            "proxy": symbol,
            "inceptionDate": registered.get("inceptionDate"),
            "dataStartDate": registered.get("dataStartDate"),
            "issuer": registered.get("issuer", "State Street" if symbol.startswith("XL") else None),
            "issuerUrl": registered.get("issuerUrl"),
        }
    return {"name": symbol, "proxy": symbol, "inceptionDate": None, "issuer": None, "issuerUrl": None}


def fetch_research_payload(symbol: str) -> dict:
    now = datetime.now(timezone.utc)
    today = now.date()
    last_complete_date = today - timedelta(days=1)
    start = today - timedelta(days=365 * 11)
    if symbol == "BTCUSD":
        try:
            btc_bars = coinbase_btc_candles(start, last_complete_date)
            source = "Coinbase Exchange BTC/USD"
        except MarketDataError:
            btc_bars = coin_metrics_btc_prices(start, last_complete_date)
            source = "Coin Metrics PriceUSD"
        series = [{"time": bar_date(bar), "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0} for bar in btc_bars]
        metrics = research_metrics(series)
        return {
            "symbol": symbol, "security": security_metadata(symbol), "benchmark": "BTC/USD", "source": source,
            "feed": "daily UTC reference", "chartType": "line", "asOf": series[-1]["time"], "bars": series,
            "trailingReturns": trailing_returns(series), "metrics": {key: value for key, value in metrics.items() if key != "drawdowns"},
            "drawdowns": metrics["drawdowns"], "calendarReturns": calendar_returns(series), "availableStart": series[0]["time"],
            "availableEnd": series[-1]["time"], "stale": False, "cacheTtlSeconds": CACHE_SECONDS,
        }
    common = {
        "timeframe": "1Day",
        "start": start.isoformat(),
        "end": (now - timedelta(minutes=20)).isoformat().replace("+00:00", "Z"),
        "limit": "10000",
        "sort": "asc",
    }
    stock_params = {**common, "symbols": symbol, "adjustment": "all", "feed": "sip"}

    stock_bars = [
        bar
        for bar in alpaca_pages("/v2/stocks/bars", stock_params, symbol)
        if date.fromisoformat(bar_date(bar)) <= last_complete_date
    ]
    try:
        btc_bars = coinbase_btc_candles(start, last_complete_date)
        btc_source = "Coinbase Exchange BTC/USD"
        chart_type = "candlestick"
        reference_type = "daily UTC OHLC"
    except MarketDataError:
        btc_bars = coin_metrics_btc_prices(start, last_complete_date)
        btc_source = "Coin Metrics PriceUSD"
        chart_type = "line"
        reference_type = "daily reference"
    series = build_ratio_series(stock_bars, btc_bars)
    if not series:
        raise MarketDataError(f"No aligned Alpaca data was returned for {symbol} and BTC/USD.")

    metrics = research_metrics(series)
    return {
        "symbol": symbol,
        "security": security_metadata(symbol),
        "benchmark": f"BTC/USD ({btc_source})",
        "source": f"Alpaca SIP equities + {btc_source}",
        "feed": reference_type,
        "chartType": chart_type,
        "asOf": series[-1]["time"],
        "bars": series,
        "trailingReturns": trailing_returns(series),
        "metrics": {key: value for key, value in metrics.items() if key != "drawdowns"},
        "drawdowns": metrics["drawdowns"],
        "calendarReturns": calendar_returns(series),
        "availableStart": series[0]["time"],
        "availableEnd": series[-1]["time"],
        "stale": (last_complete_date - date.fromisoformat(series[-1]["time"])).days > 4,
        "cacheTtlSeconds": CACHE_SECONDS,
    }


def cached_research_payload(symbol: str) -> dict:
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(symbol)
        if cached and now - cached[0] < CACHE_SECONDS:
            return cached[1]
    payload = fetch_research_payload(symbol)
    with _cache_lock:
        _cache[symbol] = (now, payload)
    return payload


def fetch_market_ticker_payload() -> dict:
    now = datetime.now(timezone.utc)
    last_complete_date = now.date() - timedelta(days=1)
    start = last_complete_date - timedelta(days=14)
    symbols = [item["symbol"] for item in MARKET_TICKER]
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start.isoformat(),
        "end": (now - timedelta(minutes=20)).isoformat().replace("+00:00", "Z"),
        "limit": "1000",
        "sort": "asc",
        "adjustment": "all",
        "feed": "sip",
    }
    stock_sets = alpaca_multi_pages("/v2/stocks/bars", params, symbols)
    try:
        btc_bars = coinbase_btc_candles(start, last_complete_date)
        btc_source = "Coinbase Exchange BTC/USD"
    except MarketDataError:
        btc_bars = coin_metrics_btc_prices(start, last_complete_date)
        btc_source = "Coin Metrics PriceUSD"

    items = []
    for definition in MARKET_TICKER:
        series = build_ratio_series(stock_sets.get(definition["symbol"], []), btc_bars)
        if not series:
            continue
        latest = series[-1]
        previous = series[-2] if len(series) > 1 else latest
        change = ((latest["close"] / previous["close"]) - 1) * 100 if previous["close"] else 0.0
        items.append({
            **definition,
            "valueKs": latest["close"] * 100_000,
            "change": change,
            "asOf": latest["time"],
        })
    if not items:
        raise MarketDataError("Market ticker data is unavailable.")
    return {
        "items": items,
        "source": f"Alpaca SIP equities + {btc_source}",
        "asOf": min(item["asOf"] for item in items),
        "cacheTtlSeconds": CACHE_SECONDS,
    }


def cached_market_ticker_payload() -> dict:
    global _ticker_cache
    now = time.monotonic()
    with _cache_lock:
        if _ticker_cache and now - _ticker_cache[0] < CACHE_SECONDS:
            return _ticker_cache[1]
    payload = fetch_market_ticker_payload()
    with _cache_lock:
        _ticker_cache = (now, payload)
    return payload


def group_registry(group: str) -> list[dict]:
    registries = {"sectors": SECTORS, "asset-classes": ASSET_CLASSES, "countries": COUNTRIES}
    if group not in registries:
        raise MarketDataError("Unknown ranking group.")
    return registries[group]


def fetch_group_payload(group: str) -> dict:
    registry = group_registry(group)
    symbols = list(dict.fromkeys(item["symbol"] for item in registry if item["symbol"] != "BTC/USD"))
    now = datetime.now(timezone.utc)
    last_complete_date = now.date() - timedelta(days=1)
    start = now.date() - timedelta(days=365 * 11)
    params = {
        "symbols": ",".join(symbols),
        "timeframe": "1Day",
        "start": start.isoformat(),
        "end": (now - timedelta(minutes=20)).isoformat().replace("+00:00", "Z"),
        "limit": "10000",
        "sort": "asc",
        "adjustment": "all",
        "feed": "sip",
    }
    stock_sets = alpaca_multi_pages("/v2/stocks/bars", params, symbols)
    try:
        btc_bars = coinbase_btc_candles(start, last_complete_date)
        btc_source = "Coinbase Exchange BTC/USD"
    except MarketDataError:
        btc_bars = coin_metrics_btc_prices(start, last_complete_date)
        btc_source = "Coin Metrics PriceUSD"

    series_by_symbol: dict[str, list[dict]] = {}
    for symbol in symbols:
        completed = [bar for bar in stock_sets[symbol] if date.fromisoformat(bar_date(bar)) <= last_complete_date]
        series = build_ratio_series(completed, btc_bars)
        if series:
            series_by_symbol[symbol] = series
    if not series_by_symbol:
        raise MarketDataError("No aligned ranking data was returned.")
    common_as_of = min(points[-1]["time"] for points in series_by_symbol.values())

    items = []
    for definition in registry:
        public_definition = {key: value for key, value in definition.items() if key != "slug"}
        if definition["symbol"] == "BTC/USD":
            returns = {label: 0.0 for label in ["YTD", "1-Year", "3-Year", "5-Year", "10-Year"]}
            items.append({**public_definition, "status": "ok", "availableStart": "2015-07-20", "returns": returns})
            continue
        series = [point for point in series_by_symbol.get(definition["symbol"], []) if point["time"] <= common_as_of]
        if not series:
            items.append({**public_definition, "status": "unavailable", "availableStart": None, "returns": {}})
            continue
        values = trailing_returns(series)
        items.append({
            **public_definition,
            "status": "ok",
            "availableStart": series[0]["time"],
            "returns": {label: values.get(label) for label in ["YTD", "1-Year", "3-Year", "5-Year", "10-Year"]},
        })
    return {
        "group": group,
        "registryVersion": REGISTRY_VERSION,
        "asOf": common_as_of,
        "source": f"Alpaca SIP equities + {btc_source}",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "cacheTtlSeconds": RANKING_CACHE_SECONDS,
        "stale": (last_complete_date - date.fromisoformat(common_as_of)).days > 4,
        "items": items,
    }


def cached_group_payload(group: str) -> dict:
    now = time.monotonic()
    with _cache_lock:
        cached = _ranking_cache.get(group)
        if cached and now - cached[0] < RANKING_CACHE_SECONDS:
            return cached[1]
    payload = fetch_group_payload(group)
    with _cache_lock:
        _ranking_cache[group] = (now, payload)
        _provider_state["rankings"] = {"ok": True, "lastSuccess": datetime.now(timezone.utc).isoformat(), "group": group}
    return payload


def clean_source_cell(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def parse_weight(value: str) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
    if not match:
        raise MarketDataError("State Street returned an invalid fund weight.")
    return float(match.group(0))


def parse_state_street_table(page: str, heading: str) -> tuple[str, list[list[str]]]:
    heading_pattern = re.escape(heading).replace(r"\ ", r"\s+")
    match = re.search(
        rf"<h3[^>]*>\s*{heading_pattern}\s*<span[^>]*class=[\"'][^\"']*date[^\"']*[\"'][^>]*>\s*as\s+of\s+([^<]+)</span>\s*</h3>.*?<table[^>]*>.*?<tbody>(.*?)</tbody>",
        page,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise MarketDataError(f"State Street's {heading.lower()} table could not be read.")

    rows: list[list[str]] = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", match.group(2), re.IGNORECASE | re.DOTALL):
        cells = [
            clean_source_cell(cell)
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.IGNORECASE | re.DOTALL)
        ]
        if cells:
            rows.append(cells)
    if not rows:
        raise MarketDataError(f"State Street's {heading.lower()} table was empty.")
    return clean_source_cell(match.group(1)), rows


def normalize_holding_name(name: str) -> str:
    overrides = {
        "META PLATFORMS INC CLASS A": "Meta Platforms Class A",
        "ALPHABET INC CL A": "Alphabet Class A",
        "ALPHABET INC CL C": "Alphabet Class C",
        "AT+T INC": "AT&T",
        "VERIZON COMMUNICATIONS INC": "Verizon Communications",
    }
    return overrides.get(name, name.title())


def parse_state_street_fund(page: str, symbol: str, source_url: str) -> dict:
    holdings_date, holding_rows = parse_state_street_table(page, "Fund Top Holdings")
    allocation_date, allocation_rows = parse_state_street_table(page, "Fund Industry Allocation")
    if holdings_date != allocation_date:
        raise MarketDataError("State Street returned mismatched fund-data dates.")
    try:
        as_of = datetime.strptime(holdings_date, "%b %d %Y").date().isoformat()
    except ValueError as exc:
        raise MarketDataError("State Street returned an invalid fund-data date.") from exc

    holdings = [
        {"name": normalize_holding_name(row[0]), "weight": parse_weight(row[-1])}
        for row in holding_rows[:5]
        if len(row) >= 2
    ]
    allocations = [
        {"name": row[0], "weight": parse_weight(row[-1])}
        for row in allocation_rows
        if len(row) >= 2
    ]
    if len(holdings) < 5 or not allocations or not 99 <= sum(item["weight"] for item in allocations) <= 101:
        raise MarketDataError("State Street returned incomplete XLC fund data.")
    return {
        "symbol": symbol,
        "asOf": as_of,
        "source": "State Street Investment Management",
        "sourceUrl": source_url,
        "industryAllocations": allocations,
        "topHoldings": holdings,
    }


def parse_state_street_xlc(page: str) -> dict:
    return parse_state_street_fund(page, "XLC", STATE_STREET_XLC_URL)


def fetch_state_street_fund(symbol: str) -> dict:
    definition = next((item for item in SECTORS if item["symbol"] == symbol), None)
    if not definition:
        raise MarketDataError("Issuer fund details are not configured for that symbol.")
    request = Request(
        definition["issuerUrl"],
        headers={"Accept": "text/html", "User-Agent": "SatValue-local/1.0"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            page = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raise MarketDataError(f"State Street returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise MarketDataError("State Street fund data is temporarily unreachable.") from exc
    payload = parse_state_street_fund(page, symbol, definition["issuerUrl"])
    payload.update({
        "fund": {key: value for key, value in definition.items() if key != "slug"},
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "stale": False,
        "refreshIntervalSeconds": FUND_CACHE_SECONDS,
    })
    return payload


def cached_state_street_fund(symbol: str) -> dict:
    now = time.monotonic()
    with _cache_lock:
        cached = _fund_cache.get(symbol)
        if cached and now - cached[0] < FUND_CACHE_SECONDS:
            return cached[1]
    try:
        payload = fetch_state_street_fund(symbol)
    except MarketDataError as exc:
        if symbol != "XLC":
            raise
        payload = {**XLC_FALLBACK, "fund": {key: value for key, value in SECTORS[0].items() if key != "slug"}}
        payload.update({"fetchedAt": None, "stale": True, "warning": f"{exc} Showing the last verified snapshot.", "refreshIntervalSeconds": FUND_CACHE_SECONDS})
    with _cache_lock:
        _fund_cache[symbol] = (now, payload)
        _provider_state["stateStreet"] = {"ok": not payload.get("stale", False), "lastSuccess": payload.get("fetchedAt"), "symbol": symbol}
    return payload


def cached_state_street_xlc() -> dict:
    return cached_state_street_fund("XLC")


class SatValueHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path_parts = [part for part in parsed.path.split("/") if part]
        if (
            any(part.startswith(".") for part in path_parts)
            or parsed.path == "/server.py"
            or parsed.path.startswith("/tests/")
        ):
            self.send_error(HTTPStatus.NOT_FOUND.value)
            return
        if parsed.path == "/api/health":
            self.send_json({
                "ok": True,
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "providers": {
                    "alpaca": _provider_state.get("alpaca", {"ok": True, "status": "not checked in this process"}),
                    "bitcoin": _provider_state.get("bitcoin", {"ok": True, "status": "not checked in this process"}),
                    "stateStreet": _provider_state.get("stateStreet", {"ok": True, "status": "not checked in this process"}),
                },
                "cachePolicy": {"seriesSeconds": CACHE_SECONDS, "rankingsSeconds": RANKING_CACHE_SECONDS, "fundSeconds": FUND_CACHE_SECONDS},
                "cacheEntries": {"series": len(_cache), "rankings": len(_ranking_cache), "funds": len(_fund_cache), "portfolios": len(_portfolio_cache), "ticker": int(_ticker_cache is not None)},
                "analytics": {"pageviews": sum(_analytics.values())},
            })
            return
        if parsed.path == "/api/registry":
            group = parse_qs(parsed.query).get("group", ["sectors"])[0]
            try:
                registry = group_registry(group)
                self.send_json({"group": group, "version": REGISTRY_VERSION, "items": [{key: value for key, value in item.items() if key != "slug"} for item in registry]})
            except MarketDataError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            return
        if parsed.path == "/api/ticker":
            try:
                self.send_json(cached_market_ticker_payload())
            except MarketDataError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            except Exception:
                self.send_json({"error": "Market ticker could not be loaded."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path == "/api/rankings":
            group = parse_qs(parsed.query).get("group", ["sectors"])[0]
            try:
                self.send_json(cached_group_payload(group))
            except MarketDataError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            except Exception:
                self.send_json({"error": "Rankings could not be loaded."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path == "/api/fund":
            symbol = parse_qs(parsed.query).get("symbol", ["XLC"])[0].strip().upper()
            if not any(item["symbol"] == symbol for item in SECTORS):
                self.send_json({"error": "Automatic fund details are not configured for that symbol."}, HTTPStatus.NOT_FOUND)
                return
            try:
                self.send_json(cached_state_street_fund(symbol))
            except MarketDataError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            except Exception:
                self.send_json({"error": "Fund details could not be loaded."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path == "/api/series":
            symbol = parse_qs(parsed.query).get("symbol", ["SPY"])[0].strip().upper()
            if not SYMBOL_PATTERN.fullmatch(symbol):
                self.send_json({"error": "Enter a valid US stock or ETF symbol."}, HTTPStatus.BAD_REQUEST)
                return
            try:
                payload = cached_research_payload(symbol)
                with _cache_lock:
                    _provider_state["alpaca"] = {"ok": True, "lastSuccess": datetime.now(timezone.utc).isoformat(), "symbol": symbol}
                    _provider_state["bitcoin"] = {"ok": True, "lastSuccess": datetime.now(timezone.utc).isoformat(), "source": payload["benchmark"]}
                self.send_json(payload)
            except MarketDataError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            except Exception:
                self.send_json({"error": "Market data could not be loaded."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/portfolio":
            try:
                payload = json.loads(read_request_body(self.headers, self.rfile, 16384))
                if not isinstance(payload, dict):
                    raise MarketDataError("Portfolio request must be a JSON object.")
                self.send_json(cached_portfolio_payload(payload))
            except (ValueError, json.JSONDecodeError, PortfolioValidationError) as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except MarketDataError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            except Exception:
                self.send_json({"error": "Portfolio backtest could not be completed."}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path != "/api/analytics":
            self.send_error(HTTPStatus.NOT_FOUND.value)
            return
        try:
            payload = json.loads(read_request_body(self.headers, self.rfile, 2048))
            page = str(payload.get("page", "unknown"))[:100]
        except (ValueError, json.JSONDecodeError, MarketDataError):
            page = "unknown"
        with _cache_lock:
            _analytics[page] = _analytics.get(page, 0) + 1
        self.send_json({"ok": True}, HTTPStatus.ACCEPTED)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.plot.ly https://s3.tradingview.com; style-src 'self' 'unsafe-inline' https://s3.tradingview.com; img-src 'self' data: https:; connect-src 'self' https:; frame-src 'self' https://s.tradingview.com https://www.tradingview-widget.com;")
        super().end_headers()


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "9000"))
    host = os.environ.get("HOST", "127.0.0.1")
    server = ReusableThreadingHTTPServer((host, port), SatValueHandler)
    print(f"SatValue running at http://{host}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
