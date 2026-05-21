# NZX & ASX Stock Monitor

A self-refreshing dashboard for NZX 50, ASX 200 and a custom watchlist. Flags any name down 5%+ in a day, plus oversold and near-52-week-low signals.

**Live URL:** *(set after you enable GitHub Pages — see SETUP.md)*

## What's in here

- `index.html` — the dashboard (this is what GitHub Pages serves)
- `prices.json` — latest market data, regenerated each run
- `fetch_prices.py` — pulls prices from Yahoo Finance + CoinGecko
- `build_dashboard.py` — turns the JSON into the HTML page
- `.github/workflows/refresh.yml` — runs the two scripts on weekdays at 7pm NZ time

## Changing the watchlist

Edit the `STOCKS` and `CRYPTOS` lists at the top of `fetch_prices.py`. Stock symbols use Yahoo Finance format (`AIR.NZ`, `CBA.AX`, `TTWO` for US). Crypto uses CoinGecko IDs (find them at coingecko.com — the ID is in the URL).

After editing, the next scheduled run will pick up the change. To regenerate immediately, open the **Actions** tab on GitHub and click "Run workflow" on the "Refresh stock monitor" job.

## Running locally

```
python3 fetch_prices.py
python3 build_dashboard.py
```

Opens `index.html` directly in any browser — no server needed.

## Not financial advice

Flags are technical signals only. A 5% drop can mean a bargain or that something's gone wrong — check the news before you act.
