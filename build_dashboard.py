"""
Reads prices.json (same folder) and writes index.html (same folder).
The HTML is fully self-contained — drop it on any web host and it works.
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_ROOT = Path(__file__).resolve().parent
data = json.loads((REPO_ROOT / "prices.json").read_text())

# --- Flagging rules ---
DROP_THRESHOLD_PCT = -5.0           # day change at or below this => drop alert
OVERSOLD_FROM_52W_PCT = -20.0       # down 20%+ from 52w high => "oversold"
NEAR_52W_LOW_PCT = 5.0              # within 5% of 52w low => "near low"


def classify(row, kind):
    tags = []
    dc = row.get("day_change_pct")
    if dc is not None and dc <= DROP_THRESHOLD_PCT:
        tags.append("drop")
    if kind == "stock":
        wh = row.get("from_52w_high_pct")
        if wh is not None and wh <= OVERSOLD_FROM_52W_PCT:
            tags.append("oversold")
        price = row.get("price")
        low = row.get("wk52_low")
        if price and low:
            pct_above_low = (price - low) / low * 100
            if 0 <= pct_above_low <= NEAR_52W_LOW_PCT:
                tags.append("near_low")
    else:
        rh = row.get("from_recent_high_pct")
        if rh is not None and rh <= OVERSOLD_FROM_52W_PCT:
            tags.append("oversold")
    return tags


for s in data["stocks"]:
    s["_tags"] = classify(s, "stock") if "error" not in s else []
for c in data["crypto"]:
    c["_tags"] = classify(c, "crypto")

GROUP_ORDER = ["Indexes", "Your picks", "Your picks (US)", "NZX 50 (top names)", "ASX 50 (top names)"]
groups: dict[str, list] = {g: [] for g in GROUP_ORDER}
for s in data["stocks"]:
    groups.setdefault(s.get("group", "Other"), []).append(s)

alerts = []
for s in data["stocks"]:
    if "drop" in s.get("_tags", []):
        alerts.append({
            "name": s["name"], "ticker": s["symbol"],
            "change": s["day_change_pct"], "price": s["price"],
            "currency": s["currency"], "tags": s["_tags"], "kind": "stock",
        })
for c in data["crypto"]:
    if "drop" in c.get("_tags", []):
        alerts.append({
            "name": c["name"], "ticker": c["ticker"],
            "change": c["day_change_pct"], "price": c["price"],
            "currency": "USD", "tags": c["_tags"], "kind": "crypto",
        })


def fmt_price(p, currency):
    if p is None: return "—"
    if currency == "USD" and p < 1: return f"{currency} {p:,.4f}"
    if p < 1: return f"{currency} {p:,.3f}"
    return f"{currency} {p:,.2f}"


def fmt_pct(p):
    if p is None: return "—"
    sign = "+" if p > 0 else ""
    return f"{sign}{p:.2f}%"


def pct_class(p):
    if p is None: return "neutral"
    if p <= DROP_THRESHOLD_PCT: return "down-big"
    if p < 0: return "down"
    if p > 0: return "up"
    return "neutral"


def sparkline_svg(values, width=80, height=24):
    if not values or len(values) < 2: return ""
    vmin, vmax = min(values), max(values)
    rng = vmax - vmin or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = i * (width / (n - 1))
        y = height - ((v - vmin) / rng) * height
        pts.append(f"{x:.1f},{y:.1f}")
    color = "#16a34a" if values[-1] >= values[0] else "#dc2626"
    return (
        f'<svg class="spark" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'preserveAspectRatio="none"><polyline fill="none" stroke="{color}" stroke-width="1.5" '
        f'points="{" ".join(pts)}"/></svg>'
    )


def tag_badges(tags):
    out = []
    if "drop" in tags:
        out.append('<span class="badge badge-drop" title="Down 5% or more today">▼ 5%+ drop</span>')
    if "oversold" in tags:
        out.append('<span class="badge badge-oversold" title="Down 20%+ from 52-week high">oversold</span>')
    if "near_low" in tags:
        out.append('<span class="badge badge-low" title="Within 5% of 52-week low">near 52w low</span>')
    return " ".join(out)


def render_stock_row(s):
    if "error" in s:
        return (f'<tr><td>{s.get("name", s["symbol"])}</td>'
                f'<td colspan="6" class="muted">data unavailable ({s["error"][:60]})</td></tr>')
    tags = s.get("_tags", [])
    row_class = "flagged" if "drop" in tags else ""
    return f"""
    <tr class="{row_class}">
      <td class="namecol">
        <div class="name">{s["name"]}</div>
        <div class="ticker">{s["symbol"]} · {s.get("listed", "")}</div>
      </td>
      <td class="num">{fmt_price(s["price"], s["currency"])}</td>
      <td class="num {pct_class(s["day_change_pct"])}">{fmt_pct(s["day_change_pct"])}</td>
      <td class="num {pct_class(s["from_52w_high_pct"])}">{fmt_pct(s["from_52w_high_pct"])}</td>
      <td class="num muted">{fmt_price(s["wk52_low"], s["currency"])} – {fmt_price(s["wk52_high"], s["currency"])}</td>
      <td class="spark-cell">{sparkline_svg(s.get("sparkline") or [])}</td>
      <td class="tags">{tag_badges(tags)}</td>
    </tr>
    """


def render_crypto_row(c):
    tags = c.get("_tags", [])
    row_class = "flagged" if "drop" in tags else ""
    return f"""
    <tr class="{row_class}">
      <td class="namecol">
        <div class="name">{c["name"]}</div>
        <div class="ticker">{c["ticker"]} · crypto</div>
      </td>
      <td class="num">{fmt_price(c["price"], "USD")}</td>
      <td class="num {pct_class(c["day_change_pct"])}">{fmt_pct(c["day_change_pct"])}</td>
      <td class="num {pct_class(c["from_recent_high_pct"])}">{fmt_pct(c["from_recent_high_pct"])}</td>
      <td class="num muted">30d high {fmt_price(c["recent_high_30d"], "USD")}</td>
      <td class="spark-cell">{sparkline_svg(c.get("sparkline") or [])}</td>
      <td class="tags">{tag_badges(tags)}</td>
    </tr>
    """


def section(title, rows_html, subtitle=""):
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    return f"""
    <section>
      <h2>{title}</h2>
      {sub}
      <div class="table-wrap"><table>
        <thead><tr>
          <th>Name</th><th class="num">Price</th><th class="num">Day Δ</th>
          <th class="num">From 52w high</th><th class="num">52w range</th>
          <th>20d trend</th><th>Flags</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table></div>
    </section>
    """


sections_html = ""
if groups.get("Indexes"):
    sections_html += section("Market indexes",
        "\n".join(render_stock_row(s) for s in groups["Indexes"]),
        "How the NZX and ASX as a whole are doing today.")
if groups.get("Your picks"):
    sections_html += section("Your picks · NZX / ASX",
        "\n".join(render_stock_row(s) for s in groups["Your picks"]))
if groups.get("Your picks (US)"):
    sections_html += section("Your picks · US listed",
        "\n".join(render_stock_row(s) for s in groups["Your picks (US)"]),
        "Take-Two trades on NASDAQ in USD.")
sections_html += section("Crypto · 24h change in USD",
    "\n".join(render_crypto_row(c) for c in data["crypto"]),
    "Crypto trades 24/7 — 'Day Δ' is the last 24 hours.")
if groups.get("NZX 50 (top names)"):
    sections_html += section("NZX 50 · top names",
        "\n".join(render_stock_row(s) for s in groups["NZX 50 (top names)"]))
if groups.get("ASX 50 (top names)"):
    sections_html += section("ASX 50 · top names",
        "\n".join(render_stock_row(s) for s in groups["ASX 50 (top names)"]))

if alerts:
    alert_chips = "\n".join(
        f'<span class="alert-chip"><strong>{a["name"]}</strong> '
        f'<span class="alert-change">{fmt_pct(a["change"])}</span></span>'
        for a in sorted(alerts, key=lambda a: a["change"])
    )
    alert_block = f"""
    <div class="alerts-banner">
      <div class="alerts-title">🔻 Drop alerts today ({len(alerts)})</div>
      <div class="alerts-sub">Names down 5% or more from yesterday's close:</div>
      <div class="alerts-chips">{alert_chips}</div>
    </div>
    """
else:
    alert_block = """
    <div class="alerts-banner alerts-quiet">
      <div class="alerts-title">No 5%+ drops in your watchlist today.</div>
      <div class="alerts-sub">Quiet day. Check back after market close.</div>
    </div>
    """

gen_dt = datetime.fromisoformat(data["generated_at_utc"])
gen_nz = gen_dt.astimezone(timezone(timedelta(hours=12)))
last_updated = gen_nz.strftime("%a %d %b %Y, %I:%M %p NZ time")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NZX &amp; ASX Stock Monitor</title>
<meta name="robots" content="noindex, nofollow">
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #fafaf9; color: #1c1917; margin: 0; padding: 24px;
    font-size: 14px; line-height: 1.5; max-width: 1100px; margin-left: auto; margin-right: auto;
  }}
  header {{ margin-bottom: 20px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; font-weight: 600; }}
  .updated {{ color: #78716c; font-size: 12px; }}
  .intro {{ color: #44403c; margin: 10px 0 0; max-width: 720px; }}
  .alerts-banner {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
    padding: 14px 16px; margin: 18px 0 24px; }}
  .alerts-banner.alerts-quiet {{ background: #f0fdf4; border-color: #bbf7d0; }}
  .alerts-title {{ font-weight: 600; color: #991b1b; font-size: 15px; }}
  .alerts-quiet .alerts-title {{ color: #166534; }}
  .alerts-sub {{ color: #78716c; font-size: 12px; margin-top: 2px; }}
  .alerts-chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
  .alert-chip {{ background: white; border: 1px solid #fca5a5; padding: 6px 10px;
    border-radius: 6px; color: #1c1917; font-size: 13px; }}
  .alert-chip strong {{ color: #991b1b; }}
  .alert-change {{ color: #b91c1c; font-weight: 600; margin-left: 6px; }}
  section {{ margin: 28px 0; }}
  h2 {{ font-size: 15px; margin: 0 0 4px; font-weight: 600; color: #1c1917; }}
  .section-sub {{ color: #78716c; font-size: 12px; margin-bottom: 10px; }}
  .table-wrap {{ background: white; border: 1px solid #e7e5e4; border-radius: 8px;
    overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #f5f5f4; }}
  tr:last-child td {{ border-bottom: none; }}
  th {{ background: #f5f5f4; font-weight: 500; font-size: 11px; text-transform: uppercase;
    color: #78716c; letter-spacing: 0.04em; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.muted, .muted {{ color: #a8a29e; }}
  .name {{ font-weight: 500; }}
  .ticker {{ color: #a8a29e; font-size: 11px; margin-top: 2px; }}
  .up {{ color: #15803d; }} .down {{ color: #b91c1c; }}
  .down-big {{ color: #b91c1c; font-weight: 600; }} .neutral {{ color: #57534e; }}
  tr.flagged {{ background: #fef9f0; }}
  tr.flagged:hover {{ background: #fef3e2; }}
  .spark-cell {{ width: 90px; }}
  .spark {{ display: block; }}
  .badge {{ display: inline-block; font-size: 10px; padding: 2px 7px; border-radius: 4px;
    margin-right: 4px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.03em; }}
  .badge-drop {{ background: #fee2e2; color: #991b1b; }}
  .badge-oversold {{ background: #fef3c7; color: #92400e; }}
  .badge-low {{ background: #ddd6fe; color: #5b21b6; }}
  footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #e7e5e4;
    color: #78716c; font-size: 11px; max-width: 720px; }}
  footer strong {{ color: #44403c; }}
</style>
</head>
<body>
<header>
  <h1>NZX &amp; ASX Stock Monitor</h1>
  <div class="updated">Last updated: <strong>{last_updated}</strong></div>
  <p class="intro">
    Tracks the NZX 50, ASX 200 and our custom watchlist. Anything that drops
    <strong>5% or more</strong> in a day gets flagged at the top.
  </p>
</header>

{alert_block}

{sections_html}

<footer>
  <strong>How to read this:</strong> <em>Day Δ</em> is today's move vs. yesterday's close.
  <em>From 52w high</em> is how far the price has fallen from its highest point in the past
  year. The little chart shows the last ~20 trading days.<br><br>
  <strong>Flags:</strong>
  <span class="badge badge-drop">▼ 5%+ drop</span> means it fell 5%+ today.
  <span class="badge badge-oversold">oversold</span> = down 20%+ from 52-week high.
  <span class="badge badge-low">near 52w low</span> = within 5% of the 52-week low.<br><br>
  <strong>Not financial advice.</strong> Flags are technical signals, not buy recommendations.
  A 5% drop can mean a bargain or that something's wrong — always check the news before
  you decide.<br><br>
  Stock data via Yahoo Finance · crypto via CoinGecko. Auto-refreshes on weekdays.
</footer>
</body>
</html>
"""

(REPO_ROOT / "index.html").write_text(html)
print(f"Wrote index.html ({len(html):,} bytes) — {len(alerts)} drop alert(s)")
for a in sorted(alerts, key=lambda a: a["change"]):
    print(f"  {a['name']:30s} {a['change']:+.2f}%")
