# Competitive Watch (JohnPac)
A lightweight, serverless-friendly competitive monitoring setup for Sigma Supply, JM Industrial, and Pratt Industries.

## What it does
- Scrapes key pages on a schedule (via GitHub Actions).
- Diffs content by CSS selector.
- Writes `data/changes.json` consumed by a static dashboard (`index.html`).
- Optionally posts alerts to Slack if `SLACK_WEBHOOK_URL` is set as a repo secret.

## Quick Start (GitHub Pages + Actions)
1. **Create a new GitHub repo** and upload these files.
2. In repo **Settings → Pages**, set:
   - Source: `Deploy from a branch`
   - Branch: `main` (or `master`) / root (`/`)
3. In **Settings → Secrets and variables → Actions → New repository secret**, add (optional):
   - `SLACK_WEBHOOK_URL` = your Slack Incoming Webhook URL (optional).
4. Commit to `main` (or `master`). The workflow runs nightly and on manual dispatch.
5. Visit your GitHub Pages site to view the dashboard (e.g., `https://<you>.github.io/<repo>/`).

## Run locally
```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scraper.py
python build_changes_index.py  # regenerates data/changes.json if needed
open index.html
```

## Files
- `index.html` — dashboard UI that reads `data/changes.json`.
- `targets.csv` — list of competitors, URLs, fields, and CSS selectors.
- `scraper.py` — fetches pages, extracts values, diffs against snapshots, appends changes.
- `build_changes_index.py` — compiles a trimmed changes feed (last 500) from `changes_log.jsonl`.
- `requirements.txt` — Python deps.
- `.github/workflows/monitor.yml` — nightly job. Saves updated JSON and commits it.
- `snapshots/` — previous values per (competitor,url,field).
- `data/` — published artifacts (served by GitHub Pages).

## Customization
- Add rows to `targets.csv` for more pages/fields.
- Tune rate limiting and user-agent in `scraper.py`.
- Switch to Playwright for JS-heavy pages (notes inline in `scraper.py`).

> Note: We target safe selectors that are likely to exist today. If a selector misses on a given page, adjust the `css_selector` in `targets.csv` — use your browser’s DevTools → Elements tab to find a stable selector.
