# Setup guide — getting your dashboard live on the web

This walks you through five steps, no command line needed. Should take 10 minutes.

End state: a URL like `https://YOURNAME.github.io/nzx-watch-pgycz0n/` that you and your nephew bookmark. It updates itself every weekday after market close.

---

## Step 1 — Create a new GitHub repository

1. Go to **https://github.com/new**.
2. **Repository name:** `nzx-watch-pgycz0n` *(I generated this random suffix so the URL isn't guessable. Use it as-is, or pick your own random-looking name.)*
3. **Visibility:** Public *(free GitHub Pages needs this — but with the random name, no one will find it unless you share the link)*.
4. Leave everything else **unchecked** (no README, no .gitignore, no license — we're bringing our own).
5. Click **Create repository**.

GitHub will land you on an empty repo page.

---

## Step 2 — Upload the files

On that empty repo page, look for the link **"uploading an existing file"** in the middle of the page. Click it.

1. Open the `stock-monitor-repo` folder I gave you.
2. **Select every file and folder inside it** (including the hidden `.github` folder — on Mac, press ⌘+⇧+. to show hidden files first; on Windows, enable "Show hidden items" in File Explorer's View menu).
3. Drag them all onto GitHub's upload area.
4. Once they finish uploading, scroll down to **"Commit changes"** and click the green **Commit changes** button.

After a moment you'll see all the files listed: `index.html`, `fetch_prices.py`, `build_dashboard.py`, `prices.json`, `README.md`, `.gitignore`, and `.github/workflows/refresh.yml`.

---

## Step 3 — Turn on GitHub Pages

1. In your repo, click the **Settings** tab (top right).
2. In the left sidebar, click **Pages**.
3. Under "Build and deployment", set:
   - **Source:** `Deploy from a branch`
   - **Branch:** `main` and `/ (root)`
4. Click **Save**.

Wait about 30 seconds, then refresh the Pages settings page. You'll see a green banner saying something like:

> Your site is live at `https://YOURNAME.github.io/nzx-watch-pgycz0n/`

**That's the URL to bookmark and send your nephew.**

---

## Step 4 — Let the scheduled refresh write back to the repo

The daily refresh needs permission to commit the updated `index.html`. One-time setup:

1. In your repo, **Settings → Actions → General**.
2. Scroll down to **Workflow permissions**.
3. Pick **Read and write permissions**.
4. Click **Save**.

---

## Step 5 — Run the refresh once to test

1. Click the **Actions** tab at the top of your repo.
2. If GitHub asks "I understand my workflows, go ahead and enable them," click that.
3. In the left sidebar, click **Refresh stock monitor**.
4. On the right, click **Run workflow** → **Run workflow**.
5. A new run appears with a yellow dot. After 30–60 seconds it goes green ✓.

Open your Pages URL again — you'll see the latest data. From now on it refreshes automatically each weekday at 7pm NZ time.

---

## How to change what's tracked

Edit `fetch_prices.py` directly on GitHub:

1. Click the file in your repo.
2. Click the pencil icon (top right).
3. Edit the `STOCKS` or `CRYPTOS` list at the top.
4. Scroll down, click **Commit changes**.
5. Go to **Actions → Refresh stock monitor → Run workflow** to apply right away (otherwise it'll wait for the next scheduled run).

Yahoo Finance tickers: NZX = `.NZ` suffix, ASX = `.AX`, US has no suffix. CoinGecko IDs live in the URL — `coingecko.com/en/coins/cardano` → ID is `cardano`.

---

## Troubleshooting

- **The Actions tab says "Workflow failed"** — click the failed run, expand the red step, screenshot the error and send it to me.
- **Pages URL shows a 404** — wait 2–3 minutes after the first commit; Pages takes a moment to publish the first time.
- **A ticker shows "data unavailable"** — Yahoo doesn't know that symbol. Check the spelling on finance.yahoo.com first.
- **Want to take it offline later?** Settings → Pages → Source → "None". Or delete the whole repo.
