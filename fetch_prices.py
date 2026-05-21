"""
Fetches current price data for the NZ/ASX/US/crypto watchlist and writes prices.json.
Stocks: Yahoo Finance public chart API. Crypto: CoinGecko free API.
Used by build_dashboard.py to produce the published index.html.

Edit the STOCKS and CRYPTOS lists below to change what's tracked.
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# WATCHLIST — edit these to add or remove tickers
# Stock format: (yahoo_ticker, display_name, group, exchange_label)
# NZX tickers end in .NZ, ASX tickers end in .AX, US tickers have no suffix.
# Yahoo index symbols start with ^ (^NZ50, ^AXJO).
# ============================================================
STOCKS = [
    # Market indexes
    ("^NZ50",  "NZX 50 Index",            "Indexes", "NZX"),
    ("^AXJO",  "ASX 200 Index",           "Indexes", "ASX"),

    # Top NZX 50 constituents
    ("FPH.NZ", "Fisher & Paykel Healthcare", "NZX 50 (top names)", "NZX"),
    ("AIA.NZ", "Auckland Intl Airport",      "NZX 50 (top names)", "NZX"),
    ("MFT.NZ", "Mainfreight",                "NZX 50 (top names)", "NZX"),
    ("MEL.NZ", "Meridian Energy",            "NZX 50 (top names)", "NZX"),
    ("CEN.NZ", "Contact Energy",             "NZX 50 (top names)", "NZX"),
    ("EBO.NZ", "EBOS Group",                 "NZX 50 (top names)", "NZX"),
    ("MCY.NZ", "Mercury NZ",                 "NZX 50 (top names)", "NZX"),
    ("RYM.NZ", "Ryman Healthcare",           "NZX 50 (top names)", "NZX"),

    # Top ASX 50 constituents
    ("CBA.AX", "Commonwealth Bank",          "ASX 50 (top names)", "ASX"),
    ("BHP.AX", "BHP Group",                  "ASX 50 (top names)", "ASX"),
    ("CSL.AX", "CSL Ltd",                    "ASX 50 (top names)", "ASX"),
    ("NAB.AX", "National Australia Bank",    "ASX 50 (top names)", "ASX"),
    ("WBC.AX", "Westpac",                    "ASX 50 (top names)", "ASX"),
    ("ANZ.AX", "ANZ Banking Group",          "ASX 50 (top names)", "ASX"),
    ("WES.AX", "Wesfarmers",                 "ASX 50 (top names)", "ASX"),
    ("MQG.AX", "Macquarie Group",            "ASX 50 (top names)", "ASX"),
    ("FMG.AX", "Fortescue",                  "ASX 50 (top names)", "ASX"),
    ("WOW.AX", "Woolworths Group",           "ASX 50 (top names)", "ASX"),
    ("TLS.AX", "Telstra",                    "ASX 50 (top names)", "ASX"),
    ("RIO.AX", "Rio Tinto",                  "ASX 50 (top names)", "ASX"),

    # Your specific picks
    ("AIR.NZ", "Air New Zealand",            "Your picks", "NZX"),
    ("SPK.NZ", "Spark New Zealand",          "Your picks", "NZX"),
    ("AAA.AX", "BetaShares Aus High Interest Cash ETF", "Your picks", "ASX"),
    ("TTWO",   "Take-Two Interactive",       "Your picks (US)", "NASDAQ"),
]

# Crypto: (coingecko_id, ticker_label, display_name)
CRYPTOS = [
    ("bitcoin",          "BTC", "Bitcoin"),
    ("hedera-hashgraph", "HBAR","Hedera"),
    ("ripple",           "XRP", "XRP (Ripple)"),
    ("stellar",          "XLM", "Stellar Lumens"),
]

UA = {"User-Agent": "Mozilla/5.0 (StockMonitor/1.0)"}
REPO_ROOT = Path(__file__).resolve().parent


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_stock(symbol: str) -> dict:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol)}?range=1mo&interval=1d"
    )
    try:
        data = http_get_json(url)
        result = data["chart"]["result"][0]
        meta = result["meta"]
        closes = result["indicators"]["quote"][0]["close"]
        timestamps = result.get("timestamp", [])
        valid = [(t, c) for t, c in zip(timestamps, closes) if c is not None]

        price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        day_change_pct = ((price - prev_close) / prev_close * 100) if (price and prev_close) else None

        wk52_high = meta.get("fiftyTwoWeekHigh")
        wk52_low = meta.get("fiftyTwoWeekLow")
        from_high_pct = ((price - wk52_high) / wk52_high * 100) if (price and wk52_high) else None

        recent_closes = [c for _, c in valid]
        recent_high = max(recent_closes) if recent_closes else None
        from_recent_high = ((price - recent_high) / recent_high * 100) if (price and recent_high) else None

        return {
            "symbol": symbol,
            "currency": meta.get("currency"),
            "exchange": meta.get("fullExchangeName"),
            "price": price,
            "prev_close": prev_close,
            "day_change_pct": day_change_pct,
            "wk52_high": wk52_high,
            "wk52_low": wk52_low,
            "from_52w_high_pct": from_high_pct,
            "recent_high_1mo": recent_high,
            "from_recent_high_pct": from_recent_high,
            "sparkline": recent_closes[-20:],
            "market_time": meta.get("regularMarketTime"),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def fetch_cryptos(ids: list[str]) -> dict:
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={','.join(ids)}&vs_currencies=usd"
        "&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true"
    )
    try:
        return http_get_json(url)
    except Exception as e:
        return {"_error": str(e)}


def fetch_crypto_history(cg_id: str) -> list[float]:
    url = (
        f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
        f"?vs_currency=usd&days=30&interval=daily"
    )
    try:
        data = http_get_json(url)
        return [p[1] for p in data.get("prices", [])][-20:]
    except Exception:
        return []


def main():
    stock_rows = []
    for sym, name, group, exch in STOCKS:
        info = fetch_stock(sym)
        info.update({"name": name, "group": group, "listed": exch})
        stock_rows.append(info)

    crypto_prices = fetch_cryptos([c[0] for c in CRYPTOS])
    crypto_rows = []
    for cg_id, ticker, name in CRYPTOS:
        d = crypto_prices.get(cg_id, {})
        spark = fetch_crypto_history(cg_id)
        recent_high = max(spark) if spark else None
        price = d.get("usd")
        from_recent_high = ((price - recent_high) / recent_high * 100) if (price and recent_high) else None
        crypto_rows.append({
            "id": cg_id,
            "ticker": ticker,
            "name": name,
            "price": price,
            "day_change_pct": d.get("usd_24h_change"),
            "vol_24h": d.get("usd_24h_vol"),
            "market_cap": d.get("usd_market_cap"),
            "from_recent_high_pct": from_recent_high,
            "recent_high_30d": recent_high,
            "sparkline": spark,
        })

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stocks": stock_rows,
        "crypto": crypto_rows,
    }
    out_path = REPO_ROOT / "prices.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {out_path} — {len(stock_rows)} stocks, {len(crypto_rows)} crypto rows.")


if __name__ == "__main__":
    main()
